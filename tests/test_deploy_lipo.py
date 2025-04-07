import subprocess
import tempfile
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

def test_deploy_lipo():
    repo = os.path.join(os.path.dirname(__file__), "..")
    run(f"conan config install {repo}")
    run("conan --help")

    txt = textwrap.dedent("""
        from conan import ConanFile
        from conan.tools.cmake import cmake_layout

        class Pkg(ConanFile):
            # Note that we don't depend on arch
            settings = "os", "compiler", "build_type"

            requires = ("libtiff/4.5.0",)

            def build(self):
                # Don't use XcodeBuild because it passes a single -arch flag
                build_type = self.settings.get_safe("build_type")
                project = 'example.xcodeproj'
                self.run('xcodebuild -configuration {} -project {} -alltargets'.format(build_type, project))
        """)
    save("conanfile.py", txt)

    run("conan install . --deploy=lipo -s arch=x86_64")
    run("conan install . --deploy=lipo_add -s arch=armv8")

    # Check that a nested dependency is present and contains two architectures
    depend_file = os.path.join("full_deploy", "host", "zlib", "1.2.13", "Release", "lib", "libz.a")
    assert os.path.exists(depend_file)
    with subprocess.Popen(["lipo", "-info", depend_file],
                          stdout=subprocess.PIPE,
                          stderr=subprocess.PIPE) as pipe:
        info = pipe.stdout.readline()
        assert info.find("x86_64") >= 0
        assert info.find("arm64") >= 0
