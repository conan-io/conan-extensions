import ast
import configparser
import hashlib
import os
import sys
import urllib
import xml.dom.minidom
from typing import List, Tuple

from conan.api.conan_api import ConanAPI
from conan.api.output import ConanOutput
from conan.cli.command import conan_command
from conan.tools.scm import Version

import requests
import yaml


@conan_command(group="Conan Center Index")
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


def get_hash_and_mirrors(version: Version, session: requests.Session) -> Tuple[str, List[str]]:
    sources_hash = None
    mirrors = []
    for archive_name in [f"qt-everywhere-opensource-src-{version}.tar.xz", f"qt-everywhere-src-{version}.tar.xz"]:
        link = f"https://download.qt.io/official_releases/qt/{version.major}.{version.minor}/{version}/single/{archive_name}"
        with session.head(link) as req:
            if req.ok:
                break
    else:
        ConanOutput().error(f"Could not download metalink for version {version}")
        sys.exit(-1)
    mirrors.append(link)
    mirrors.append(f"https://download.qt.io/archive/qt/{version.major}.{version.minor}/{version}/single/{archive_name}")
    with session.get(f"{link}.meta4") as req:
        req.raise_for_status()
        tree = xml.dom.minidom.parseString(req.text).documentElement
        if tree.tagName != "metalink":
            ConanOutput().error(f"meta link root tag incorrect: expected \"metalink\" but got {tree.tagName}")
            sys.exit(-1)
        files = tree.getElementsByTagName("file")
        if not len(files) == 1:
            ConanOutput().error(f"Could not find `file` tag in {link}.meta4 file content")
            sys.exit(-1)
        file = files[0]
        hash_elements = file.getElementsByTagName("hash")
        for hash_element in hash_elements:
            if hash_element.getAttribute("type") == "sha-256":
                sources_hash = hash_element.firstChild.nodeValue
                break
        else:
            ConanOutput().error(f"Could not find hash tag in {link}.meta4 file content")
            sha256_hash = hashlib.sha256()
            with urllib.request.urlopen(link) as f:
                # Read and update hash string value in blocks of 4K
                for byte_block in iter(lambda: f.read(4096),b""):
                    sha256_hash.update(byte_block)
            sources_hash = sha256_hash.hexdigest()
        mirrors.extend(node.firstChild.nodeValue for node in file.getElementsByTagName("url") if node.firstChild.nodeValue)
    return sources_hash, mirrors


def recipe_folder(version: Version) -> str:
    return f"{version.major}.x.x"


def update_conandata_yml(version: Version, sources_hash: str, mirrors: List[str]) -> None:

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
                lines.extend(f"      - \"{m}\"\n" for m in mirrors)
                lines.append(f"    sha256: \"{sources_hash}\"\n")
                sources_inserted = True

            if not patches_inserted and line.startswith("patches:"):
                lines.append(f"  \"{version}\":\n")
                lines.extend(f"    {line}\n" for line in yaml.safe_dump(patches, default_style='"', default_flow_style=False).splitlines())
                sources_inserted = True
    with open(conan_data_yml_path, 'w') as conandata_file:
        conandata_file.writelines(lines)


def create_modules_file(version: Version, session: requests.Session) -> None:
    for tag in [f"v{version}-lts-lgpl", f"v{version}"]:
        with session.get(f"https://code.qt.io/cgit/qt/qt5.git/plain/.gitmodules?h=refs/tags/{tag}") as req:
            if req.ok:
                with open(f"{recipe_folder(version)}/qtmodules{version}.conf", 'w') as f:
                    f.write(req.text)
                return
    else:
        ConanOutput().error(f"Could not find tag for version \"{version}\"")
        sys.exit(-1)


def update_conanfile(version: Version) -> None:
    existing_modules = get_existing_modules(version)
    missing_modules = [m for m in get_new_modules(version) if m not in existing_modules]

    if not missing_modules:
        return

    line = insertion_line(version)

    with open(f"{recipe_folder(version)}/conanfile.py") as f:
        recipe = f.readlines()

    with open(f"{recipe_folder(version)}/conanfile.py", "w") as f:
        f.writelines(recipe[0:line])
        f.write("    _submodules += [")
        f.write(", ".join(f'"{m}"' for m in missing_modules))
        f.write(f"] # new modules for qt {version}\n")
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
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if target.id == "_submodules":
                    submodules_node = node
        elif isinstance(node, ast.AugAssign):
            if node.target.id == "_submodules":
                submodules_node = node
    if not submodules_node:
        ConanOutput().error(f"Could not find _submodules assignment in recipe \"{recipe_folder(version)}/conanfile.py\"")
        sys.exit(-1)

    return submodules_node.end_lineno


def get_new_modules(version: Version) -> List[str]:
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


def get_existing_modules(version: Version) -> List[str]:
    with open(f"{recipe_folder(version)}/conanfile.py") as f:
        recipe = f.read()
    _locals = locals()
    exec(recipe, globals(), _locals)
    return _locals["QtConan"]()._submodules
