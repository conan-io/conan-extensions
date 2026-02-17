import json
import tempfile
import textwrap
import os
import datetime
import re

import pytest

from tools import load, save, run


@pytest.fixture(autouse=True)
def conan_test():
    old_env = dict(os.environ)
    conan_home = tempfile.mkdtemp(suffix='conans')
    env_vars = {"CONAN_HOME": conan_home}
    os.environ.update(env_vars)
    current = tempfile.mkdtemp(suffix="conans")
    cwd = os.getcwd()
    os.chdir(current)

    repo = os.path.join(os.path.dirname(__file__), "..")
    run(f"conan config install {repo}")
    run("conan profile detect")
    try:
        yield
    finally:
        os.chdir(cwd)
        os.environ.clear()
        os.environ.update(old_env)


def _fake_conan_sources(graph):
    # Fake the existence of conan_sources.tgz file to avoid contacting Artifactory for the tests
    for _, node in graph["nodes"].items():
        recipe_folder = node.get("recipe_folder")
        if recipe_folder:
            fake_sources_tgz_path = os.path.join(os.path.dirname(node.get("recipe_folder")), "d", "conan_sources.tgz")
            save(fake_sources_tgz_path, "")


def test_static_library_skip_binaries():
    """
    Test skip binaries behavior with static and shared libraries
    """
    run("conan new cmake_lib -d name=lib1 -d version=1.0")
    conanfile = load("conanfile.py")
    conanfile = conanfile.replace('package_type = "library"', 'package_type = "static-library"')
    save("conanfile.py", conanfile)
    run("conan create .")

    run("conan new cmake_lib -d name=lib2 -d version=1.0 -d requires=lib1/1.0 --force")
    conanfile = load("conanfile.py")
    conanfile = conanfile.replace('package_type = "library"', 'package_type = "shared-library"')
    #conanfile = conanfile.replace('self.requires("liba/1.0")', 'self.requires("liba/1.0", transitive_libs=True)')
    save("conanfile.py", conanfile)
    run("conan create . -o lib2/*:shared=True")

    run("conan new cmake_lib -d name=lib3 -d version=1.0 -d requires=lib2/1.0 --force")

    run("conan create . -o lib2/1.0:shared=True -f json > create.json")
    graph = json.loads(load("create.json"))["graph"]
    assert graph["nodes"]["3"]["binary"] == "Skip"
    assert graph["nodes"]["3"]["package_folder"] is None

    _fake_conan_sources(graph)
    out = run("conan art:build-info create create.json build_name 1 repo --with-dependencies > bi.json")
    assert "WARN: Package is marked as 'Skip' for lib1/1.0" in out
    build_info = json.loads(load("bi.json"))
    assert "lib3/1.0" in build_info["modules"][1]["id"].split(":")[0]  # libc package
    # Remove package id and rrev leave them as "<name>/<version> :: <file>" to make the asserts platform agnostic
    dependencies_ids = [f"{dep['id'].split('#')[0]} ::{dep['id'].split('::')[-1]}" for dep in build_info["modules"][1]["dependencies"]]
    assert len(dependencies_ids) == 2  # liba package files are not present as binary is skipped
    assert "lib2/1.0 :: conaninfo.txt" in dependencies_ids
    assert "lib2/1.0 :: conanmanifest.txt" in dependencies_ids

    run("conan create . -o lib2/1.0:shared=True -c:a tools.graph:skip_binaries=False -f json > create.json")
    graph = json.loads(load("create.json"))["graph"]
    assert graph["nodes"]["3"]["binary"] == "Cache"
    assert graph["nodes"]["3"]["package_folder"] is not None

    _fake_conan_sources(graph)
    out = run("conan art:build-info create create.json build_name 1 repo --with-dependencies > bi.json")
    assert "WARN: Package is marked as 'Skip' for lib1/1.0" not in out
    build_info = json.loads(load("bi.json"))
    assert "lib3/1.0" in build_info["modules"][1]["id"].split(":")[0]  # libc package
    # Remove package id and rrev leave them as "<name>/<version>#rrev :: <file>" to make the asserts platform agnostic
    dependencies_ids = [f"{dep['id'].split('#')[0]} ::{dep['id'].split('::')[-1]}" for dep in build_info["modules"][1]["dependencies"]]
    assert len(dependencies_ids) == 4  # liba package files now should be present
    assert "lib2/1.0 :: conaninfo.txt" in dependencies_ids
    assert "lib2/1.0 :: conanmanifest.txt" in dependencies_ids
    assert "lib1/1.0 :: conaninfo.txt" in dependencies_ids
    assert "lib1/1.0 :: conanmanifest.txt" in dependencies_ids


def test_tool_require_skip_binaries():
    """
    Test skip binaries behavior on tool require added as cache dependency
    """
    conanfile = textwrap.dedent("""
        from conan import ConanFile

        class Meson(ConanFile):
            name = "meson"
            version = 1.0
            package_type = "application"

            def package_info(self):
                self.cpp_info.includedirs = []
                self.cpp_info.libdirs = []
                self.cpp_info.bindirs = []
        """)
    save(os.path.join(os.curdir, "conanfile.py"), conanfile)
    run("conan create .")

    run("conan new cmake_lib -d name=libb -d version=1.0 --force")
    conanfile = load("conanfile.py")
    conanfile = conanfile.replace('package_type = "library"',
                                  'package_type = "static-library"\n    tool_requires = "meson/1.0"')
    save("conanfile.py", conanfile)
    run("conan create .")

    run("conan new cmake_lib -d name=libc -d version=1.0 -d requires=libb/1.0 --force")

    run("conan create . -f json > create.json")

    graph = json.loads(load("create.json"))["graph"]
    assert graph["nodes"]["3"]["binary"] == "Skip"
    assert graph["nodes"]["3"]["package_folder"] is None

    # Set package revision to null to simulate issue https://github.com/conan-io/conan-extensions/issues/170
    graph["nodes"]["3"]["prev"] = None
    save("create.json", json.dumps({"graph": graph}))

    _fake_conan_sources(graph)
    out = run("conan art:build-info create create.json build_name 1 repo --add-cached-deps --with-dependencies > bi.json")
    assert "WARN: Package is marked as 'Skip' for meson/1.0" in out
    bi = load("bi.json")
    build_info = json.loads(bi)
    # Check libb recipe depends on meson recipe
    assert "meson" in build_info["modules"][2]["dependencies"][0]["id"]
    # Check libb package has no dependencies (meson package not in cache bc is was skipped as not needed)
    assert len(build_info["modules"][3]["dependencies"]) == 0

    run("conan create . -c:a tools.graph:skip_binaries=False -f json > create.json")
    graph = json.loads(load("create.json"))["graph"]
    assert graph["nodes"]["3"]["binary"] == "Cache"
    assert graph["nodes"]["3"]["package_folder"] is not None

    _fake_conan_sources(graph)
    out = run(
        "conan art:build-info create create.json build_name 1 repo --add-cached-deps --with-dependencies > bi.json")
    assert "WARN: Package is marked as 'Skip' for meson/1.0" not in out
    bi = load("bi.json")
    build_info = json.loads(bi)
    # Check libb recipe depends on meson recipe
    assert "meson" in build_info["modules"][2]["dependencies"][0]["id"]
    # Check libb package now has the meson dependency
    build_info["modules"][3]["dependencies"]
    assert len(build_info["modules"][3]["dependencies"]) == 2


def test_build_info_with_metadata_files():
    """
    Test that metadata files are added to the build info
    """
    conanfile = textwrap.dedent("""
        import os
        from conan import ConanFile
        from conan.tools.files import save

        class Recipe(ConanFile):
            name = "pkg-w-metadata"
            version = 1.0

            def export(self):
                save(self, os.path.join(self.recipe_metadata_folder, "logs", "extra_info.txt"), "some info")

            def build(self):
                save(self, os.path.join(self.package_metadata_folder, "logs", "build.log"), "srclog!!")
        """)
    save(os.path.join(os.curdir, "conanfile.py"), conanfile)
    run("conan create . -f json > create.json")

    graph = json.loads(load("create.json"))["graph"]
    _fake_conan_sources(graph)

    run("conan art:build-info create create.json build_name 1 danimtb-local > bi.json")
    build_info = json.loads(load("bi.json"))
    # recipe module
    assert build_info['modules'][0]['artifacts'][3]['name'] == "extra_info.txt"
    assert "/export/metadata/logs/extra_info.txt" in build_info['modules'][0]['artifacts'][3]['path']
    # package module
    assert build_info['modules'][1]['artifacts'][2]['name'] == "build.log"
    assert "/metadata/logs/build.log" in build_info['modules'][1]['artifacts'][2]['path']
    run("conan art:build-info create create.json build_name 1 repo --with-dependencies > bi.json")


def test_formatted_time():
    """Compare local timestamp hours from build-info JSON with current timestamp in UTC"""
    run("conan new cmake_lib -d name=lib1 -d version=1.0")
    run("conan create . -f json > create.json")

    graph = json.loads(load("create.json"))["graph"]
    _fake_conan_sources(graph)

    run("conan art:build-info create create.json build_name 1 danimtb-local > bi.json")
    build_info = json.loads(load("bi.json"))
    timestamp = build_info["started"]

    # Parse the timestamp and convert to UTC
    # Format is like: 2025-11-25T14:11:25.980+0100 (3-digit milliseconds, timezone without colon)
    # Use regex to capture all parts
    pattern = r'(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2}):(\d{2})\.(\d{3})([+-]\d{4})'
    match = re.match(pattern, timestamp)
    assert match, f"Timestamp format does not match expected pattern: {timestamp}"

    year, month, day, hour, minute, second, millis, tz_str = match.groups()

    # Create datetime object
    dt = datetime.datetime(int(year), int(month), int(day), int(hour), int(minute), int(second), int(millis) * 1000)

    # Parse timezone offset like +0100 or -0500
    tz_sign = tz_str[0]
    tz_hours = int(tz_str[1:3])
    tz_minutes = int(tz_str[3:5])
    tz_offset = datetime.timedelta(hours=tz_hours, minutes=tz_minutes)
    if tz_sign == '-':
        tz_offset = -tz_offset
    tz_info = datetime.timezone(tz_offset)
    timestamp_utc = dt.replace(tzinfo=tz_info).astimezone(datetime.timezone.utc)

    # Get current UTC time and compare within the same hour
    current_utc = datetime.datetime.now(datetime.timezone.utc)
    assert timestamp_utc.replace(minute=0, second=0, microsecond=0) == \
           current_utc.replace(minute=0, second=0, microsecond=0)


def test_missing_files_warning():
    """
    Test that there are no warnings about missing .tgz files
    """
    run("conan new header_lib -d name=lib1 -d version=1.0")
    run("conan create . -f json > create.json")
    graph = json.loads(load("create.json"))["graph"]
    _fake_conan_sources(graph)
    run("conan upload lib1/1.0 -r conancenter --dry-run")  # Simulate upload to generate the expected .tgz files

    out = run("conan art:build-info create create.json build_name 1 repo --with-dependencies > bi.json")
    assert not "WARN: There are missing .tgz files" in out
