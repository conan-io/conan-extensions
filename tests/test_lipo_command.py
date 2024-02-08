import sys
import tempfile
import textwrap
import os

from tools import load, save, run

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


@pytest.mark.skipif(sys.platform != "darwin", reason="Universal binaries tests only for macOS")
def test_lipo_create():
    repo = os.path.join(os.path.dirname(__file__), "..")
    run(f"conan config install {repo}")
    run("conan --help")
    run("conan new cmake_lib -d name=require -d version=1.0")
    run("conan create . -tf="" -s arch=armv8")
    run("conan create . -tf="" -s arch=x86_64")
    run("conan new cmake_lib -d name=mylibrary -d version=1.0 -d requires=require/1.0 --force")
    run("conan create . -tf="" -s arch=armv8")
    run("conan create . -tf="" -s arch=x86_64")
    run("conan install --requires=mylibrary/1.0 --deployer=full_deploy -s arch=armv8")
    run("conan install --requires=mylibrary/1.0 --deployer=full_deploy -s arch=x86_64")
    run("conan bin:lipo full_deploy -a x86_64 -a armv8")

