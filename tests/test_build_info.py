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


def test_static_library_skip_binaries():
    """
    Test skip binaries behavior with static and shared libraries
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
    out = run("conan art:build-info create create.json build_name 1 repo --with-dependencies > bi.json")
    assert "WARN: There are missing artifacts" in out
    assert "WARN: Package liba/1.0#ca2698d8aec856e057f4513f6c3cb2d1 is marked as 'Skip'" in out
    build_info = json.loads(load("bi.json"))
    assert "libc/1.0#95c7f81c13006116d5f1abc3f58af7f8" in build_info["modules"][1]["id"].split(":")[0]  # libc package
    # Remove package id and rrev leave them as "<name>/<version>#rrev :: <file>" to make the asserts platform agnostic
    dependencies_ids = [f"{dep['id'].split(':')[0]} ::{dep['id'].split('::')[-1]}" for dep in build_info["modules"][1]["dependencies"]]
    assert len(dependencies_ids) == 2  # liba package files are not present as binary is skipped
    assert "libb/1.0#be341ee6c860d01aa8e8458e482d1293 :: conaninfo.txt" in dependencies_ids
    assert "libb/1.0#be341ee6c860d01aa8e8458e482d1293 :: conanmanifest.txt" in dependencies_ids

    run("conan create . -o libb/1.0:shared=True -c tools.graph:skip_binaries=False -f json > create.json")
    graph = json.loads(load("create.json"))["graph"]
    assert graph["nodes"]["3"]["binary"] == "Cache"
    assert graph["nodes"]["3"]["package_folder"] is not None
    out = run("conan art:build-info create create.json build_name 1 repo --with-dependencies > bi.json")
    assert "WARN: There are missing artifacts" not in out
    assert "WARN: Package liba/1.0#ca2698d8aec856e057f4513f6c3cb2d1 is marked as 'Skip'" not in out
    build_info = json.loads(load("bi.json"))
    assert "libc/1.0#95c7f81c13006116d5f1abc3f58af7f8" in build_info["modules"][1]["id"].split(":")[0]  # libc package
    # Remove package id and rrev leave them as "<name>/<version>#rrev :: <file>" to make the asserts platform agnostic
    dependencies_ids = [f"{dep['id'].split(':')[0]} ::{dep['id'].split('::')[-1]}" for dep in build_info["modules"][1]["dependencies"]]
    assert len(dependencies_ids) == 4  # liba package files now should be present
    assert "libb/1.0#be341ee6c860d01aa8e8458e482d1293 :: conaninfo.txt" in dependencies_ids
    assert "libb/1.0#be341ee6c860d01aa8e8458e482d1293 :: conanmanifest.txt" in dependencies_ids
    assert "liba/1.0#ca2698d8aec856e057f4513f6c3cb2d1 :: conaninfo.txt" in dependencies_ids
    assert "liba/1.0#ca2698d8aec856e057f4513f6c3cb2d1 :: conanmanifest.txt" in dependencies_ids
