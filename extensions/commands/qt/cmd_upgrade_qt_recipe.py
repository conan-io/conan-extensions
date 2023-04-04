import xml.etree.ElementTree as ET

from conan.api.conan_api import ConanAPI
from conan.api.output import ConanOutput
from conan.cli.command import conan_command
from conan.tools.scm import Version

import requests
import yaml

@conan_command(group="Extension")
def upgrade_qt_recipe(conan_api: ConanAPI, parser, *args):
    """
    command creating a new version of the qt recipe
    """
    
    parser.add_argument("version", help="version of qt to add to the recipe")
    args = parser.parse_args(*args)

    version = Version(args.version)

    with requests.Session() as session:
        update_config_yml(version)
        sources_hash, mirrors = get_hash_and_mirrors(version, session)
        update_conandata_yml(version, sources_hash, mirrors)
        create_modules_file(version, session)

    ConanOutput().success(f"qt version {version} successfully added to {recipe_folder(version)}.\n"
                          "You may have to manually add new modules to recipe's `_submodules` member.")

    
def update_config_yml(version: Version) -> None:
    with open("config.yml", "r") as config_file:
        config = yaml.safe_load(config_file)
        if str(version) in config["versions"]:
            ConanOutput().error(f"version \"{version}\" already present in config.yml")
            exit(-1)

    lines = []
    with open('config.yml') as config_file:
        inserted = False
        for line in config_file:
            if not inserted and line.startswith(f"  \"{version.major}."):
                lines.append(f"  \"{version}\":\n")
                lines.append(f"    folder: {recipe_folder(version)}\n")
                inserted = True
            lines.append(line)
    with open('config.yml', 'w') as config_file:
        config_file.writelines(lines)


def get_hash_and_mirrors(version: Version, session: requests.Session) -> tuple[str, list[str]]:
    sources_hash = None
    mirrors = []
    if version.major == 5:
        archive_name = f"qt-everywhere-opensource-src-{version}.tar.xz"
    else:
        archive_name = f"qt-everywhere-src-{version}.tar.xz"

    link = f"https://download.qt.io/official_releases/qt/{version.major}.{version.minor}/{version}/single/{archive_name}"
    mirrors.append(link)
    mirrors.append(f"https://download.qt.io/archive/qt/{version.major}.{version.minor}/{version}/single/{archive_name}")
    with session.get(f"{link}.meta4") as req:
        req.raise_for_status()
        tree = ET.fromstring(req.text)
        if tree.tag != "{urn:ietf:params:xml:ns:metalink}metalink":
            ConanOutput().error(f"meta link root tag incorrect: expected \"metalink\" but got {tree.tag}")
            exit(-1)
        file = tree.find("{urn:ietf:params:xml:ns:metalink}file")
        if not file:
            ConanOutput().error(f"Could not find `file` tag in {link}.meta4 file content")
            exit(-1)
        sources_hash = file.find("{urn:ietf:params:xml:ns:metalink}hash[@type='sha-256']").text
        mirrors.extend(node.text for node in file.findall("{urn:ietf:params:xml:ns:metalink}url"))
    return sources_hash,mirrors

def recipe_folder(version:Version) -> str:
    return f"{version.major}.x.x"

def update_conandata_yml(version: Version, sources_hash: str, mirrors: list[str])->None:

    conan_data_yml_path = f"{recipe_folder(version)}/conandata.yml"
    
    with open(conan_data_yml_path, "r") as conandata_file:
        conandata = yaml.safe_load(conandata_file)
        if str(version) in conandata["sources"]:
            ConanOutput().error(f"version \"{version}\" already present in conandata.yml sources")
            exit(-1)
        if str(version) in conandata["patches"]:
            ConanOutput().error(f"version \"{version}\" already present in conandata.yml patches")
            exit(-1)
        patches = list(conandata["patches"].values())[0]

    lines = []
    with open(conan_data_yml_path) as conandata_file:
        sources_inserted = False
        patches_inserted = False
        for line in conandata_file:
            lines.append(line)
            if not sources_inserted and line.startswith("sources:"):
                lines.append(f"  \"{version}\":\n")
                lines.append("    url:\n")
                for m in mirrors:
                    lines.append(f"      - \"{m}\"\n")
                lines.append(f"    sha256: \"{sources_hash}\"\n")
                sources_inserted = True

            if not patches_inserted and line.startswith("patches:"):
                lines.append(f"  \"{version}\":\n")
                for l in yaml.safe_dump(patches, default_style='"', default_flow_style=False).splitlines():
                    lines.append(f"    {l}\n")
                sources_inserted = True
    with open(conan_data_yml_path, 'w') as conandata_file:
        conandata_file.writelines(lines)

def create_modules_file(version:Version, session:requests.Session) -> None:
    if version.major == 5:
        tag = f"v{version}-lts-lgpl"
    else:
        tag = f"v{version}"
    with session.get(f"https://code.qt.io/cgit/qt/qt5.git/plain/.gitmodules?h=refs/tags/{tag}") as req:
        req.raise_for_status()
        with open(f"{recipe_folder(version)}/qtmodules{version}.conf", 'w') as f:
            f.write(req.text)
