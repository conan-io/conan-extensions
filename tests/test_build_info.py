import json
import tempfile
import textwrap
import os

import pytest

from tools import load, save, run


@pytest.fixture(autouse=True)
def conan_test():
    old_env = dict(os.environ)
    env_vars = {"CONAN_HOME": tempfile.mkdtemp(suffix='conans')}
    os.environ.update(env_vars)
    current = tempfile.mkdtemp(suffix="conans")
    cwd = os.getcwd()
    os.chdir(current)
    try:
        yield
    finally:
        os.chdir(cwd)
        os.environ.clear()
        os.environ.update(old_env)


def test_skip_binaries():
    """
    Test skip binaries behavior
    """
    repo = os.path.join(os.path.dirname(__file__), "..")
    run(f"conan config install {repo}")
    run("conan profile detect")

    run("conan new cmake_lib -d name=liba -d version=1.0")
    conanfile = load("conanfile.py")
    conanfile = conanfile.replace('package_type = "library"', 'package_type = "static-library"')
    save("conanfile.py", conanfile)
    run("conan create .")

    run("conan new cmake_lib -d name=libb -d version=1.0 -d requires=liba/1.0 --force")
    conanfile = load("conanfile.py")
    conanfile = conanfile.replace('package_type = "library"', 'package_type = "shared-library"')
    save("conanfile.py", conanfile)
    run("conan create . -o libb/*:shared=True")

    run("conan new cmake_lib -d name=libc -d version=1.0 -d requires=libb/1.0 --force")

    run("conan create . -o libb/1.0:shared=True -f json > create.json")
    graph = json.loads(load("create.json"))["graph"]
    assert graph["nodes"]["3"]["binary"] == "Skip"
    assert graph["nodes"]["3"]["package_folder"] is None
    out = run("conan art:build-info create create.json build_name 1 repo --with-dependencies --skip-missing-sources", error=True)
    "Package not found" in out

    run("conan create . -o libb/1.0:shared=True -c tools.graph:skip_binaries=False -f json > create.json")
    run("conan art:build-info create create.json build_name 1 repo --with-dependencies --skip-missing-sources > bi.json")
