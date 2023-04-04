import ast
import configparser
import os
import sys
import xml.etree.ElementTree

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

    if not os.path.isdir(recipe_folder(version)):
        ConanOutput().error(f"Recipe folder could not be found in {recipe_folder(version)}")
        sys.exit(-1)

    with requests.Session() as session:
        update_config_yml(version)
        sources_hash, mirrors = get_hash_and_mirrors(version, session)
        update_conandata_yml(version, sources_hash, mirrors)
        create_modules_file(version, session)
        try:
            update_conanfile(version)
        except:
            ConanOutput().error("Could not automatically add new modules. You may have to manually add new modules to recipe's `_submodules` member")

    ConanOutput().success(f"qt version {version} successfully added to {recipe_folder(version)}.\n")


def update_config_yml(version: Version) -> None:
    with open("config.yml", "r") as config_file:
        config = yaml.safe_load(config_file)
        if str(version) in config["versions"]:
            ConanOutput().error(f"version \"{version}\" already present in config.yml")
            sys.exit(-1)

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
        tree = xml.etree.ElementTree.fromstring(req.text)
        if tree.tag != "{urn:ietf:params:xml:ns:metalink}metalink":
            ConanOutput().error(f"meta link root tag incorrect: expected \"metalink\" but got {tree.tag}")
            sys.exit(-1)
        file = tree.find("{urn:ietf:params:xml:ns:metalink}file")
        if not file:
            ConanOutput().error(f"Could not find `file` tag in {link}.meta4 file content")
            sys.exit(-1)
        sources_hash = file.find("{urn:ietf:params:xml:ns:metalink}hash[@type='sha-256']").text
        mirrors.extend(node.text for node in file.findall("{urn:ietf:params:xml:ns:metalink}url"))
    return sources_hash,mirrors


def recipe_folder(version: Version) -> str:
    return f"{version.major}.x.x"


def update_conandata_yml(version: Version, sources_hash: str, mirrors: list[str]) -> None:

    conan_data_yml_path = f"{recipe_folder(version)}/conandata.yml"

    with open(conan_data_yml_path, "r") as conandata_file:
        conandata = yaml.safe_load(conandata_file)
        if str(version) in conandata["sources"]:
            ConanOutput().error(f"version \"{version}\" already present in conandata.yml sources")
            sys.exit(-1)
        if str(version) in conandata["patches"]:
            ConanOutput().error(f"version \"{version}\" already present in conandata.yml patches")
            sys.exit(-1)
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


def create_modules_file(version: Version, session: requests.Session) -> None:
    if version.major == 5:
        tag = f"v{version}-lts-lgpl"
    else:
        tag = f"v{version}"
    with session.get(f"https://code.qt.io/cgit/qt/qt5.git/plain/.gitmodules?h=refs/tags/{tag}") as req:
        req.raise_for_status()
        with open(f"{recipe_folder(version)}/qtmodules{version}.conf", 'w') as f:
            f.write(req.text)


def update_conanfile(version: Version) -> None:
    existing_modules = get_existing_modules(version)
    missing_modules = []
    for m in get_new_modules(version):
        if m not in existing_modules:
            missing_modules.append(m)

    if not missing_modules:
        return

    line = insertion_line(version)

    with open(f"{recipe_folder(version)}/conanfile.py") as f:
        recipe = f.readlines()

    with open(f"{recipe_folder(version)}/conanfile.py", "w") as f:
        f.writelines(recipe[0:line])
        f.write("    _submodules.extend([")
        f.write(",".join(f'"{m}"' for m in missing_modules))
        f.write(f"]) # new modules for qt {version}\n")
        f.writelines(recipe[line:])


def insertion_line(version):
    with open(f"{recipe_folder(version)}/conanfile.py") as f:
        recipe = f.read()
    node = ast.parse(recipe)

    qt_conan_node = None
    for node in node.body:
        if isinstance(node, ast.ClassDef) and node.name == "QtConan":
            qt_conan_node = node
            break
    if not qt_conan_node:
        ConanOutput().error(f"Could not find QtConan class definition in recipe \"{recipe_folder(version)}/conanfile.py\"")
        sys.exit(-1)

    submodules_node = None
    for node in qt_conan_node.body:
        if not isinstance(node, ast.Assign):
            continue
        for target in node.targets:
            if target.id == "_submodules":
                submodules_node = node
    if not submodules_node:
        ConanOutput().error(f"Could not find _submodules assignment in recipe \"{recipe_folder(version)}/conanfile.py\"")
        sys.exit(-1)

    return submodules_node.end_lineno


def get_new_modules(version: Version) -> list[str]:
    config = configparser.ConfigParser()
    config.read(f"{recipe_folder(version)}/qtmodules{version}.conf")
    new_modules = []
    if not config.sections():
        ConanOutput().error(f"no qtmodules.conf file for version {version}")
        sys.exit(-1)
    for s in config.sections():
        section = str(s)
        if not section.startswith("submodule "):
            ConanOutput().error(f"qtmodules.conf section does not start with \"submodule \": {section}")
            sys.exit(-1)

        if section.count('"') != 2:
            ConanOutput().error(f"qtmodules.conf section should contain two double quotes: {section}")
            sys.exit(-1)

        modulename = section[section.find('"') + 1: section.rfind('"')]
        status = str(config.get(section, "status"))
        if status not in ("obsolete", "ignore") and modulename not in ["qtbase", "qtqa", "qtrepotools"]:
            new_modules.append(modulename)
    return new_modules


def get_existing_modules(version: Version) -> list[str]:
    with open(f"{recipe_folder(version)}/conanfile.py") as f:
        recipe = f.read()
    _locals = locals()
    exec(recipe, globals(), _locals)
    return _locals["QtConan"]()._submodules
