import tempfile
import os

import pytest

@pytest.fixture(autouse=True)
def conan_test():
    old_env = dict(os.environ)
    env_vars = {"CONAN_HOME": tempfile.mkdtemp(suffix='conans')} 
    os.environ.update(env_vars)
    try:
        yield
    finally:
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

def test_convert_txt():
    run("conan config install .")
    run("conan --help")

    
