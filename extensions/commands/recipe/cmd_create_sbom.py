import json
from packageurl import PackageURL

from conan.api.output import cli_out_write
from conan.api.conan_api import ConanAPI
from conan.cli.command import conan_command


def licenses(id):
    """
    see https://cyclonedx.org/docs/1.4/json/#components_items_licenses
    """
    if id is None:
        return []
    else:
        return [{"license": {
            "id": id
        }}]


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
    qualifiers["repository_url"] = node["remote"] if node["remote"] else "https://center.conan.io"
    return PackageURL(
        type="conan",
        name=node["name"],
        version=node["version"],
        qualifiers=qualifiers)


def component(n: dict) -> dict:
    """
    see https://cyclonedx.org/docs/1.4/json/#components
    """
    result = {
        "type": "library",
        "bom-ref": n["id"],
        "purl": package_url(n).to_string(),
        "licenses": licenses(n["license"]),
        "name": n["name"],
        "version": n["version"]
    }
    if n["description"]:
        result["description"] = n["description"]
    if n["homepage"]:
        result["externalReferences"] = [{
            "url": n["homepage"],
            "type": "website"
        }]
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
    deps.pop("0")
    cyclonedx = {
        "$schema": "http://cyclonedx.org/schema/bom-1.4.schema.json",  # https not allowed here, see schema
        "bomFormat": "CycloneDX",
        "specVersion": "1.4",
        "version": 1,
        "dependencies": [{
            "ref": n
        } for n in deps],
        "components": [component(n) for n in deps.values()]
    }
    json_result = json.dumps(cyclonedx, indent=4)
    cli_out_write(json_result)
