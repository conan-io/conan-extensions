import datetime
import json
import os
from pathlib import Path
import re
import hashlib

import requests

from conan.api.conan_api import ConanAPI
from conan.api.output import cli_out_write
from conan.cli.command import conan_command, conan_subcommand
from conan.errors import ConanException
from conans.model.recipe_ref import RecipeReference
from conan import conan_version


def response_to_str(response):
    content = response.content
    try:
        # A bytes message, decode it as str
        if isinstance(content, bytes):
            content = content.decode()

        content_type = response.headers.get("content-type")

        if content_type == "application/json":
            # Errors from Artifactory looks like:
            #  {"errors" : [ {"status" : 400, "message" : "Bla bla bla"}]}
            try:
                data = json.loads(content)["errors"][0]
                content = "{}: {}".format(data["status"], data["message"])
            except Exception:
                pass
        elif "text/html" in content_type:
            content = "{}: {}".format(response.status_code, response.reason)

        return content

    except Exception:
        return response.content


def get_export_path_from_rrev(rrev):
    ref = RecipeReference.loads(rrev)
    return f"_/{ref.name}/{ref.version}/_/{ref.revision}/export"


def get_hash(type, file_path):
    with open(file_path, "rb") as f:
        digest = hashlib.file_digest(f, type)
    return digest.hexdigest() 


def get_rrev_artifacts(node):
    artifacts = []
    recipe_folder = node.get("recipe_folder")
    dl_folder = Path(recipe_folder).parents[0] / "d"
    # TODO: throw error if d is empty? Force that the artifacts where uploaded before getting the BuildInfo?
    for file_path in dl_folder.glob("*"):
        if file_path.is_file():
            file_name = file_path.name
            artifacts.append({"name": file_name,
                                "type": os.path.splitext(file_name)[1].lstrip('.'),
                                "path": f'{get_export_path_from_rrev(node.get("ref"))}/{file_name}',
                                "sha256": get_hash("sha256", file_path),
                                "sha1": get_hash("sha1", file_path),
                                "md5": get_hash("md5", file_path)})
    return artifacts


def get_modules(json):
    ret = []
    try:
        nodes = json["graph"]["nodes"]
    except KeyError:
        raise ConanException("JSON does not contain graph information")

    for node in nodes:
        ref = node.get("ref")
        if ref and ref != "conanfile":
            module = {
                "type": "conan",
                "id": str(ref),
                "artifacts": get_rrev_artifacts(node)
            }
            ret.append(module)
    return ret


def create_build_info(data, build_name, build_number):

    properties = {
        "name": build_name,
        "number": build_number
    }

    now = datetime.datetime.now(datetime.timezone.utc)
    local_tz_offset = now.astimezone().strftime('%z')
    formatted_time = now.strftime(
        '%Y-%m-%dT%H:%M:%S.%f')[:-3] + local_tz_offset

    #if local_tz_offset == "+0000":
    #    formatted_time = formatted_time[:-5] + "Z"

    # from here: https://github.com/jfrog/build-info-go/blob/9b6f2ec13eedc41ad0f66882e630c2882f90cc76/buildinfo-schema.json#L63
    if not re.match(r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}.\d{3}(Z|[+-]\d{4})$', formatted_time):
        raise ValueError(
            "Time format does not match BuildInfo required format.")

    ret = {"version": "1.0.1",
           "name": properties.get("name"),
           "number": properties.get("number"),
           "agent": {},
           "started": formatted_time,
           "buildAgent": {"name": "conan", "version": f"{str(conan_version)}"},
           "modules": get_modules(data)}

    return json.dumps(ret, indent=4)


@conan_command(group="Custom commands")
def build_info(conan_api: ConanAPI, parser, *args):
    """
    Manages JFROG BuildInfo
    """


@conan_subcommand()
def build_info_create(conan_api: ConanAPI, parser, subparser, *args):
    """
    Creates BuildInfo from a Conan graph json from a conan install or create.
    """

    subparser.add_argument("json", help="Conan generated JSON output file.")
    subparser.add_argument("name", help="Build name property for BuildInfo.")
    subparser.add_argument(
        "number", help="Build number property for BuildInfo.")
    args = parser.parse_args(*args)

    with open(args.json, 'r') as f:
        data = json.load(f)

    info = create_build_info(data, args.name, args.number)

    cli_out_write(info)


@conan_subcommand()
def build_info_upload(conan_api: ConanAPI, parser, subparser, *args):
    """
    Uploads BuildInfo json to repository.
    """

    subparser.add_argument("build_info", help="BuildInfo json file.")
    subparser.add_argument(
        "url", help="Artifactory url, like: https://<address>/artifactory")
    subparser.add_argument("--user", help="user name for the repository")
    subparser.add_argument("--password", help="password for the user name")
    subparser.add_argument("--apikey", help="apikey for the repository")
    args = parser.parse_args(*args)

    url = args.url
    user = args.user
    password = args.password
    apikey = args.apikey

    with open(args.build_info) as json_data:
        request_url = f"{url.rstrip('/')}/api/build"
        if user and password:
            response = requests.put(request_url, headers={"Content-Type": "application/json"},
                                    data=json_data, auth=(user, password))
        elif apikey:
            response = requests.put(request_url, headers={"Content-Type": "application/json",
                                                          "X-JFrog-Art-Api": apikey},
                                    data=json_data)
        else:
            response = requests.put(request_url)

        if response.status_code == 401:
            raise Exception(response_to_str(response))
        elif response.status_code != 204:
            raise Exception(response_to_str(response))
