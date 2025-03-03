import json
import tempfile
import textwrap
import os

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
