import importlib.metadata
import json
import xml.dom.minidom
import os
import pytest
import tempfile
import textwrap

from tools import save, run

REQ_LIB = "gmp"
REQ_VER = "6.2.1"
REQ_DEP = "m4"


def cyclonedx_major_version_is_4() -> int:
    return importlib.metadata.version('cyclonedx-python-lib')[0] == '4'


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


def _test_generated_sbom_json(sbom, test_metadata_name, spec_version):
    assert sbom["bomFormat"] == "CycloneDX"
    assert sbom["specVersion"] == spec_version

    assert "metadata" in sbom
    assert "component" in sbom["metadata"]
    if test_metadata_name:
        assert sbom["metadata"]["component"]["name"] == "TestPackage"

    assert "components" in sbom
    assert len([c for c in sbom["components"] if c["name"] == REQ_LIB and c["version"] == REQ_VER]) == 1
    assert len([c for c in sbom["components"] if c["name"] == REQ_DEP]) == 1


def _test_generated_sbom_xml(sbom, test_metadata_name, spec_version):
    def with_ns(key: str) -> str:
        ns = "ns0:" if cyclonedx_major_version_is_4() else ""
        return ns + key

    schema = sbom.getAttribute("xmlns:ns0" if cyclonedx_major_version_is_4() else "xmlns")
    assert "cyclonedx" in schema
    assert schema.split("/")[-1] == spec_version

    if spec_version not in ['1.1', '1.0']:
        metadata = sbom.getElementsByTagName(with_ns("metadata"))
        assert metadata
        component = metadata[0].getElementsByTagName(with_ns("component"))
        assert component
        if test_metadata_name:
            assert component[0].getElementsByTagName(with_ns("name"))[0].firstChild.nodeValue == "TestPackage"

    components = sbom.getElementsByTagName(with_ns("components"))
    assert components
    components = components[0].getElementsByTagName(with_ns("component"))
    assert components
    assert 1 == len([
        c for c in components if
        c.getElementsByTagName(with_ns("name"))[0].firstChild.nodeValue == REQ_LIB
        and
        c.getElementsByTagName(with_ns("version"))[0].firstChild.nodeValue == REQ_VER
    ])
    assert 1 == len([
        c for c in components if
        c.getElementsByTagName(with_ns("name"))[0].firstChild.nodeValue == REQ_DEP
    ])


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


params = []
for version in ['1.4', '1.3', '1.2', '1.1', '1.0']:
    for ft in ['xml', 'json']:
        if ft == 'json' and version in ['1.1', '1.0']:
            continue
        params.append((create_conanfile_py(), "conanfile.py", ".", True, f"{version}_{ft}"))
        params.append((create_conanfile_txt(), "conanfile.txt", ".", False, f"{version}_{ft}"))
        params.append((str(), "doesnotmatter.txt", f"--requires {REQ_LIB}/{REQ_VER}", False, f"{version}_{ft}"))


@pytest.mark.parametrize("conanfile_content,conanfile_name,sbom_command,test_metadata_name,sbom_format", params)
def test_create_sbom(conanfile_content, conanfile_name, sbom_command, test_metadata_name, sbom_format):
    repo = os.path.join(os.path.dirname(__file__), "..")
    run(f"conan config install {repo}")
    run("conan profile detect")
    save(conanfile_name, conanfile_content)

    run("conan remote update --insecure conancenter")
    out = run(f"conan sbom:cyclonedx --format {sbom_format} {sbom_command}", stderr=None)
    if sbom_format.split('_')[1] == "json":
        sbom = json.loads(out)
        _test_generated_sbom_json(sbom, test_metadata_name, sbom_format.split('_')[0])
    else:
        dom = xml.dom.minidom.parseString(out).firstChild
        _test_generated_sbom_xml(dom, test_metadata_name, sbom_format.split('_')[0])
