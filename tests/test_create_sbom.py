import json
import os
import pytest
import tempfile
import textwrap

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


def test_create_sbom():
    repo = os.path.join(os.path.dirname(__file__), "..")
    run(f"conan config install {repo}")
    run("conan profile detect")
    txt = textwrap.dedent("""
        from conan import ConanFile
        from conan.tools.cmake import cmake_layout

        class Pkg(ConanFile):
            generators = "CMakeToolchain", "CMakeDeps"
            name = "TestPackage"

            def requirements(self):
                self.requires("gmp/6.2.1")

            def layout(self):
                cmake_layout(self)

            """)
    save("conanfile.py", txt)

    run("conan recipe:create-sbom . > sbom.json")
    sbom = json.loads(load("sbom.json"))

    assert sbom["bomFormat"] == "CycloneDX"
    assert sbom["specVersion"] == "1.4"

    assert "metadata" in sbom
    assert "component" in sbom["metadata"]
    assert sbom["metadata"]["component"]["name"] == "TestPackage"

    assert "components" in sbom
    assert len([c for c in sbom["components"] if c["name"] == "gmp" and c["version"] == "6.2.1"]) == 1
    assert len([c for c in sbom["components"] if c["name"] == "m4"]) == 1
