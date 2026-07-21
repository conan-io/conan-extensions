import json
import os
import tempfile
import textwrap

import pytest

from tools import save, run


ALL_POLICIES = ["lru", "oldest", "largest"]


@pytest.fixture(autouse=True)
def conan_test():
    old_env = dict(os.environ)
    env_vars = {"CONAN_HOME": tempfile.mkdtemp(suffix='conans')}
    os.environ.update(env_vars)
    current = tempfile.mkdtemp(suffix="conans")
    cwd = os.getcwd()
    os.chdir(current)
    try:
        repo = os.path.join(os.path.dirname(__file__), "..")
        run(f"conan config install {repo}")
        run("conan profile detect")
        yield
    finally:
        os.chdir(cwd)
        os.environ.clear()
        os.environ.update(old_env)


# A recipe whose package payload size is controlled by an option, so tests can build
# packages of known, distinct sizes and assert deterministic eviction behavior.
CONANFILE = textwrap.dedent("""
    from conan import ConanFile
    from conan.tools.files import save
    import os
    class Pkg(ConanFile):
        options = {"size": ["ANY"]}
        default_options = {"size": 1000}
        def package(self):
            save(self, os.path.join(self.package_folder, "payload.bin"),
                 "x" * int(self.options.size))
    """)


class TestCleanSizeWithPackages:
    """Tests that need a populated cache. The fixture builds alpha (~400KB) first and
    beta (~500KB) second, so alpha is both the oldest-created and least-recently-used."""

    @pytest.fixture(autouse=True)
    def create_packages(self, conan_test):
        save("conanfile.py", CONANFILE)
        run("conan create . --name=alpha --version=1.0 -o size=400000")
        run("conan create . --name=beta --version=1.0 -o size=500000")

    # --- Policy-specific behavior: which package is evicted first ---

    def test_lru_evicts_least_recently_used_first(self):
        # Default policy is lru. alpha is the older (less recently used) => it goes, not beta.
        out = run("conan cache:clean-size --max-size 650000B --dry-run")
        assert "alpha/1.0" in out
        assert "beta/1.0" not in out

    def test_oldest_evicts_oldest_created_first(self):
        # alpha was created first => oldest (fifo) evicts it, not beta.
        out = run("conan cache:clean-size --max-size 650000B --policy oldest --dry-run")
        assert "alpha/1.0" in out
        assert "beta/1.0" not in out

    def test_largest_evicts_biggest_first(self):
        # beta is bigger => largest evicts it, not alpha.
        out = run("conan cache:clean-size --max-size 650000B --policy largest --dry-run")
        assert "beta/1.0" in out
        assert "alpha/1.0" not in out

    def test_recipes_are_never_removed(self):
        # Prune so aggressively (1 byte) that every package binary must go. The recipe
        # revisions must survive even though they now hold no binaries and are, at that point,
        # the only thing consuming space: this command only ever removes package binaries.
        out = run("conan cache:clean-size --max-size 1B --confirm")
        assert "Removed 2 package binaries" in out
        # Both recipe revisions are still in the cache, just with no binaries left
        listing = run('conan list "*:*"')
        assert "alpha/1.0" in listing
        assert "beta/1.0" in listing
        assert "No packages found for this revision" in listing
        # And the recipe folder is still on disk / resolvable
        assert "alpha" in run("conan cache path alpha/1.0")

    def test_zero_bytes_evicts_all_binaries_but_keeps_recipes(self):
        # '0B' is explicit (so it bypasses the forgotten-unit guard) and asks for an empty
        # cache. Since recipes are never removed, it evicts ALL binaries and then warns that
        # it cannot get down to 0 because the recipe/source folders remain.
        out = run("conan cache:clean-size --max-size 0B --confirm")
        assert "Removed 2 package binaries" in out
        assert "Could not get below the limit" in out
        # All binaries gone, both recipe revisions still present
        listing = run('conan list "*:*"')
        assert "No packages found for this revision" in listing
        assert "alpha/1.0" in listing and "beta/1.0" in listing

    # --- Flag combinations, exercised against every policy ---

    @pytest.mark.parametrize("policy", ALL_POLICIES)
    def test_within_limit_removes_nothing(self, policy):
        out = run(f"conan cache:clean-size --max-size 10GB --policy {policy}")
        assert "within the size limit" in out

    @pytest.mark.parametrize("policy", ALL_POLICIES)
    def test_dry_run_reports_but_keeps_packages(self, policy):
        out = run(f"conan cache:clean-size --max-size 650000B --policy {policy} --dry-run")
        assert "Would remove" in out
        assert "dry-run, nothing deleted" in out
        # Nothing was actually removed: a second dry-run still sees the same over-limit cache
        out2 = run(f"conan cache:clean-size --max-size 650000B --policy {policy} --dry-run")
        assert "Would remove" in out2

    @pytest.mark.parametrize("policy", ALL_POLICIES)
    def test_older_than_stops_once_size_cleared(self, policy):
        # 'older-than 0s' makes BOTH packages eligible for eviction, yet removal must stop
        # as soon as the cache is under the limit: only one package goes, whichever the
        # policy picks, and the other survives despite also matching the filter.
        out = run(f"conan cache:clean-size --max-size 650000B --policy {policy} "
                  f"--older-than 0s --dry-run")
        assert "Would remove 1 package binaries" in out

    @pytest.mark.parametrize("policy", ALL_POLICIES)
    def test_older_than_protects_recently_used(self, policy):
        # Everything was just created, so a 1-day safe-harbor protects all candidates
        out = run(f"conan cache:clean-size --max-size 650000B --policy {policy} "
                  f"--older-than 1d --dry-run")
        assert "protected" in out.lower()
        assert "Would remove" not in out

    @pytest.mark.parametrize("policy", ALL_POLICIES)
    def test_real_prune_gets_under_limit(self, policy):
        run(f"conan cache:clean-size --max-size 650000B --policy {policy} --confirm")
        # After the real prune, the cache is under the limit
        out = run(f"conan cache:clean-size --max-size 650000B --policy {policy} --dry-run")
        assert "within the size limit" in out

    @pytest.mark.parametrize("policy", ALL_POLICIES)
    def test_confirmation_is_requested(self, policy):
        # Without --confirm, a non-interactive run must refuse to remove silently
        out = run(f"conan cache:clean-size --max-size 650000B --policy {policy} "
                  f"-cc core:non_interactive=True", error=True)
        assert "interactive" in out.lower()
        # The packages are still there
        out2 = run(f"conan cache:clean-size --max-size 650000B --policy {policy} --dry-run")
        assert "Would remove" in out2

    @pytest.mark.parametrize("policy", ALL_POLICIES)
    def test_json_format(self, policy):
        out = run(f"conan cache:clean-size --max-size 650000B --policy {policy} --dry-run -f json")
        # The JSON object is the last thing printed on stdout
        data = json.loads(out[out.index("{"):out.rindex("}") + 1])
        assert data["dry_run"] is True
        assert data["policy"] == policy
        assert data["max_size"] == 650000
        assert len(data["removed"]) == 1


# Argument-parsing / empty-cache tests that do not need a populated cache.

def test_max_size_is_required():
    # No default: without --max-size the command refuses to run (it never wipes the whole
    # cache implicitly). --policy alone only chooses the eviction order, not whether to clean.
    out = run("conan cache:clean-size --policy lru", error=True)
    assert "required" in out.lower()
    assert "--max-size" in out


def test_invalid_size():
    out = run("conan cache:clean-size --max-size banana", error=True)
    assert "Invalid size" in out


def test_invalid_age():
    out = run("conan cache:clean-size --max-size 1GB --older-than 5x", error=True)
    assert "Invalid age" in out


def test_invalid_policy():
    out = run("conan cache:clean-size --max-size 1GB --policy biggest", error=True)
    assert "invalid choice" in out.lower()


def test_small_unitless_number_rejected():
    # '50' without a unit is a likely typo (meant 50GB?) and would wipe the cache
    out = run("conan cache:clean-size --max-size 50 --dry-run", error=True)
    assert "forgotten unit" in out
    out_zero = run("conan cache:clean-size --max-size 0 --dry-run", error=True)
    assert "forgotten unit" in out_zero


def test_explicit_small_bytes_allowed():
    # With an explicit unit the user is trusted, even for tiny sizes
    out = run("conan cache:clean-size --max-size 100B --dry-run")
    assert "forgotten unit" not in out


def test_large_unitless_bytes_allowed():
    # A large bare byte count is a plausible real limit, not a typo
    out = run("conan cache:clean-size --max-size 5000000000 --dry-run")
    assert "forgotten unit" not in out
