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


def test_convert_txt():
    repo = os.path.join(os.path.dirname(__file__), "..")
    run(f"conan config install {repo}")
    run("conan --help")
    txt = textwrap.dedent("""
        [requires]
        hello/0.1

        [test_requires]
        gtest/1.0

        [tool_requires]
        cmake/3.15
        ninja/1.0

        [generators]
        CMakeToolchain
        CMakeDeps

        [layout]
        cmake_layout

        [options]
        hello*:shared=True
        """)
    save("conanfile.txt", txt)
    run("conan migrate:convert-txt . > conanfile.py")
    conanfile_py = load("conanfile.py")
    expected = textwrap.dedent("""\
        from conan import ConanFile
        from conan.tools.cmake import cmake_layout

        class Pkg(ConanFile):
            generators = "CMakeToolchain", "CMakeDeps",
            default_options = {'hello*:shared': 'True'}

            def requirements(self):
                self.requires("hello/0.1")

            def build_requirements(self):
                self.test_requires("gtest/1.0")
                self.tool_requires("cmake/3.15")
                self.tool_requires("ninja/1.0")

            def layout(self):
                cmake_layout(self)

        """)
    assert conanfile_py == expected
