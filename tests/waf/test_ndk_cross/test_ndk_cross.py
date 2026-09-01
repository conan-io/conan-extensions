import shutil
import tempfile
import os, sys

import pytest

from tools import run

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

def test_waf_ndk_cross():
    repo = os.path.join(os.path.dirname(__file__), "../../..")
    run(f"conan config install {repo}")
    run("conan --help")
    run("conan profile detect")
    
    os.chdir(os.path.dirname(__file__))
    run(f"{sys.executable} ../waf distclean")
    
    run("conan install . -of=build -pr:h=./android_arm64.profile -pr:b=default --build=missing")
    run(f"{sys.executable} ../waf configure build -v")
    # TODO: check if output lib matches profile arch
