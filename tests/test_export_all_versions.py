import tempfile
import textwrap
import os

import pytest

from tools import save, run


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


def test_convert_txt():
    repo = os.path.join(os.path.dirname(__file__), "..")
    run(f"conan config install {repo}")
    run("conan --help")
    conanfile = textwrap.dedent("""
        from conan import ConanFile
        
        class Pkg(ConanFile):
            name = "%s"
        """)

    config = textwrap.dedent("""
        versions:
          "0.1":
            folder: "all"
          "1.0":
            folder: "all"
    """)
    os.mkdir("recipes")

    os.mkdir("recipes/pkga")
    save("recipes/pkga/config.yml", config)
    os.mkdir("recipes/pkga/all")
    save("recipes/pkga/all/conanfile.py", conanfile % "pkga")

    os.mkdir("recipes/pkgb")
    save("recipes/pkgb/config.yml", config)
    os.mkdir("recipes/pkgb/all")
    save("recipes/pkgb/all/conanfile.py", conanfile % "pkgb")

    run("conan cci:export-all-versions -p recipes")

    assert len(os.listdir(os.path.join(os.environ.get("CONAN_HOME"), "p"))) == 6
