import json
from packageurl import PackageURL
from cyclonedx.factory.license import LicenseFactory
from cyclonedx.model import ExternalReference, ExternalReferenceType, LicenseChoice, XsUri
from cyclonedx.model.bom import Bom
from cyclonedx.model.component import Component, ComponentType
from cyclonedx.output.json import JsonV1Dot4

from conan.api.output import cli_out_write
from conan.api.conan_api import ConanAPI
from conan.cli.command import conan_command


lFac = LicenseFactory()


def package_type_to_component_type(pt: str) -> ComponentType:
    if pt is "application":
        return ComponentType.APPLICATION
    else:
        return ComponentType.LIBRARY


def licenses(id):
    """
    see https://cyclonedx.org/docs/1.4/json/#components_items_licenses
    """
    if id is None:
        return None
    else:
        return [LicenseChoice(license=lFac.make_from_string(id))]


def package_url(node: dict) -> PackageURL:
    """
    Creates a PURL following https://github.com/package-url/purl-spec/blob/master/PURL-TYPES.rst#conan
    """
    qualifiers = {
        "prev": node["prev"]
    }
    if node["user"]:
        qualifiers["user"] = node["user"]
    if node["channel"]:
        qualifiers["channel"] = node["channel"]
    if "#" in node["ref"]:
        qualifiers["rref"] = node["ref"].split("#")[1]
    if node["remote"]:  # "https://center.conan.io" is default can be omitted
        qualifiers["repository_url"] = node["remote"]
    return PackageURL(
        type="conan",
        name=node["name"],
        version=node["version"],
        qualifiers=qualifiers)


def create_component(n):
    result = Component(
        type=package_type_to_component_type(n["package_type"]),
        name=n["name"],
        version=n["version"],
        licenses=licenses(n["license"]),
        bom_ref=package_url(n).to_string(),
        purl=package_url(n),
        description=n["description"]
    )
    if n["homepage"]:
        result.external_references.add(ExternalReference(
            type=ExternalReferenceType.WEBSITE,
            url=XsUri(n["homepage"]),
        ))
    return result


@conan_command(group="Recipe")
def create_sbom(conan_api: ConanAPI, parser, *args):
    """
    creates an SBOM in CycloneDX 1.4 JSON format from a Conan graph JSON
    """
    parser.add_argument("graph_json", help="Path to Conan generated graph JSON output file.")
    args = parser.parse_args(*args)
    with open(args.graph_json, 'r') as f:
        data = json.load(f)
    deps = data["graph"]["nodes"]

    root = deps.pop("0")
    root_component = create_component(root)
    bom = Bom()
    bom.metadata.component = root_component
    for n in deps.values():
        component = create_component(n)
        bom.components.add(component)
        bom.register_dependency(root_component, [component])
    serialized_json = JsonV1Dot4(bom).output_as_string()
    cli_out_write(serialized_json)
