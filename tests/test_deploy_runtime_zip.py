import tempfile
import textwrap
import os

import pytest

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


def run(cmd):
    ret = os.system(cmd)
    if ret != 0:
        raise Exception(f"Failed CMD: {cmd}")


def save(f, content):
    with open(f, "w") as f:
        f.write(content)

def load(f):
    with open(f, "r") as f:
        return f.read()

def test_deploy_runtime_zip():
    repo = os.path.join(os.path.dirname(__file__), "..")
    run(f"conan config install {repo}")
    run("conan --help")
    run("conan new cmake_exe --define name=hello --define version=0.1")
    run("conan profile detect")
    run("conan create .")

    run("conan install --requires hello/0.1 --deploy=runtime_zip")
    assert True


    
