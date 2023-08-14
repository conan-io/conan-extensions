import json
import os
import pytest
import tempfile
import textwrap

from tools import save, run

REQ_LIB = "gmp"
REQ_VER = "6.2.1"
REQ_DEP = "m4"


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


def _test_generated_sbom(sbom, test_metadata_name):
    assert sbom["bomFormat"] == "CycloneDX"
    assert sbom["specVersion"] == "1.4"

    assert "metadata" in sbom
    assert "component" in sbom["metadata"]
    if test_metadata_name:
        assert sbom["metadata"]["component"]["name"] == "TestPackage"

    assert "components" in sbom
    assert len([c for c in sbom["components"] if c["name"] == REQ_LIB and c["version"] == REQ_VER]) == 1
    assert len([c for c in sbom["components"] if c["name"] == REQ_DEP]) == 1


def create_conanfile_txt():
    return textwrap.dedent(f"""
    [requires]
    {REQ_LIB}/{REQ_VER}
    """)


def create_conanfile_py():
    return textwrap.dedent(f"""
        from conan import ConanFile
        from conan.tools.cmake import cmake_layout

        class Pkg(ConanFile):
            generators = "CMakeToolchain", "CMakeDeps"
            name = "TestPackage"

            def requirements(self):
                self.requires("{REQ_LIB}/{REQ_VER}")

            def layout(self):
                cmake_layout(self)

            """)


@pytest.mark.parametrize("conanfile_content,conanfile_name,sbom_command,test_metadata_name", [
    (create_conanfile_py(), "conanfile.py", ".", True),
    (create_conanfile_txt(), "conanfile.txt", ".", False),
    (str(), "doesnotmatter.txt", f"--requires {REQ_LIB}/{REQ_VER}", False)
])
def test_create_sbom_cdx14json(conanfile_content, conanfile_name, sbom_command, test_metadata_name):
    repo = os.path.join(os.path.dirname(__file__), "..")
    run(f"conan config install {repo}")
    run("conan profile detect")
    save(conanfile_name, conanfile_content)

    # discard all STD_ERR(2)
    out = run(f"conan recipe:create-sbom -f cyclonedx_1.4_json {sbom_command} 2>/dev/null")
    sbom = json.loads(out)
    _test_generated_sbom(sbom, test_metadata_name)


@pytest.mark.parametrize("conanfile_content,conanfile_name,sbom_command,test_metadata_name", [
    (create_conanfile_py(), "conanfile.py", ".", True),
    (create_conanfile_txt(), "conanfile.txt", ".", False),
    (str(), "doesnotmatter.txt", f"--requires {REQ_LIB}/{REQ_VER}", False)
])
def test_create_sbom_text(conanfile_content, conanfile_name, sbom_command, test_metadata_name):
    repo = os.path.join(os.path.dirname(__file__), "..")
    run(f"conan config install {repo}")
    run("conan profile detect")
    save(conanfile_name, conanfile_content)

    # discard all STD_OUT(1)
    out_err = run(f"conan recipe:create-sbom {sbom_command} >/dev/null", True)
    assert "Format 'text' not supported" in out_err
