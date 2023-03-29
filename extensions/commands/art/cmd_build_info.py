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


def api_request(type, request_url, user=None, password=None, apikey=None, json_data=None):

    headers = {}
    if json_data:
        headers.update({"Content-Type": "application/json"})
    if apikey:
        headers.update({"X-JFrog-Art-Api": apikey})

    requests_method = getattr(requests, type)
    if user and password:
        response = requests_method(request_url, auth=(
            user, password), data=json_data, headers=headers)
    elif apikey:
        response = requests_method(
            request_url, data=json_data, headers=headers)
    else:
        response = requests_method(request_url)

    if response.status_code == 401:
        raise Exception(response_to_str(response))
    elif response.status_code not in [200, 204]:
        raise Exception(response_to_str(response))

    return response_to_str(response)


def get_remote_path(rrev, package_id=None, prev=None):
    ref = RecipeReference.loads(rrev)
    rev_path = f"_/{ref.name}/{ref.version}/_/{ref.revision}"
    if not package_id:
        return f"{rev_path}/export"
    else:
        assert prev
        return f"{rev_path}/package/{package_id}/{prev}"


def get_hashes(file_path):
    BUF_SIZE = 65536

    md5 = hashlib.md5()
    sha1 = hashlib.sha1()
    sha256 = hashlib.sha256()

    with open(file_path, 'rb') as f:
        while True:
            data = f.read(BUF_SIZE)
            if not data:
                break
            md5.update(data)
            sha1.update(data)
            sha256.update(data)
    return md5.hexdigest(), sha1.hexdigest(), sha256.hexdigest()


def get_artifacts(cache_folder, remote_path):
    artifacts = []
    dl_folder = Path(cache_folder).parents[0] / "d"
    # TODO: throw error if d is empty? Force that the artifacts where uploaded before getting the BuildInfo?
    for file_path in dl_folder.glob("*"):
        if file_path.is_file():
            file_name = file_path.name
            md5, sha1, sha256 = get_hashes(file_path)
            artifacts.append({"name": file_name,
                              "type": os.path.splitext(file_name)[1].lstrip('.'),
                              "path": f'{remote_path}/{file_name}',
                              "sha256": sha256,
                              "sha1": sha1,
                              "md5": md5})
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
            remote_path = get_remote_path(ref)
            module = {
                "type": "conan",
                "id": str(ref),
                "artifacts": get_artifacts(node.get("recipe_folder"), remote_path)
            }
            ret.append(module)
        if node.get("package_id") and node.get("prev"):
            remote_path = get_remote_path(ref, node.get("package_id"), node.get("prev"))
            module = {
                "type": "conan",
                "id": f'{str(ref)}:{node.get("package_id")}#{node.get("prev")}',
                "artifacts": get_artifacts(node.get("package_folder"), remote_path)
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

    # Apparently if the timestamp has the Z the BuildInfo is not correctly identified in Artifactory
    # if local_tz_offset == "+0000":
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


    with open(args.build_info) as f:
        payload = json.dumps(json.load(f))

    request_url = f"{args.url}/api/build"
    api_request("put", request_url, args.user, args.password,
                args.apikey, json_data=payload)
