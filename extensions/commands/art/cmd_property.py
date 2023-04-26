import json
from pathlib import Path

import requests

from conan.api.conan_api import ConanAPI
from conan.cli.command import conan_command, conan_subcommand
from conans.model.recipe_ref import RecipeReference
from conans.model.package_ref import PkgReference
from conan.errors import ConanException


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


def get_path_from_ref(ref):
    try:
        package_ref = PkgReference.loads(ref)
        recipe_ref = package_ref.ref
    except ConanException:
        recipe_ref = RecipeReference.loads(ref)
        package_ref = None

    rrev_path = f"/_/{recipe_ref.revision}" if recipe_ref.revision else ""
    pkgid_path = f"/package/{package_ref.package_id}" if package_ref and package_ref.package_id else ""
    prev_path = f"/{package_ref.revision}" if package_ref and package_ref.revision else ""
    return f"_/{recipe_ref.name}/{recipe_ref.version}{rrev_path}{pkgid_path}{prev_path}"


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


def add_default_arguments(subparser):
    subparser.add_argument("url", help="Artifactory url, like: https://<address>/artifactory")
    subparser.add_argument("repository", help="Artifactory repository.")
    subparser.add_argument("reference", help="Conan reference.")
    subparser.add_argument("--user", help="user name for the repository")
    subparser.add_argument("--password", help="password for the user name")
    subparser.add_argument("--apikey", help="apikey for the repository")
    subparser.add_argument("--property", action='append',
                           help='Property to add, like --property="build.name=buildname" --property="build.number=1"')

    return subparser


@conan_command(group="Custom commands")
def property(conan_api: ConanAPI, parser, *args):
    """
    Manages artifacts properties in Artifactory.
    """


@conan_subcommand()
def property_add(conan_api: ConanAPI, parser, subparser, *args):
    """
    Append properties for artifacts under a Conan reference recursively.
    """

    add_default_arguments(subparser)

    args = parser.parse_args(*args)

    # TODO: do we want to add properties to folders? it's slower but when
    # we set properties recursive the folders are also set, so setting also
    # for folders for consistency and check what to do
    list_folders = "1"

    # get artifacts recursively from a starting path
    root_path = get_path_from_ref(args.reference)

    request_url = f"{args.url}/api/storage/{args.repository}/{root_path}?list&deep=1&listFolders={list_folders}"

    data = json.loads(api_request("get", request_url,
                      args.user, args.password, args.apikey))

    # just consider those artifacts that have conan in the name
    # conan_artifacts = [artifact for artifact in data.get("files") if "conan" in artifact.get('uri')]

    # get properties for all artifacts
    for artifact in data.get("files"):
        uri = artifact.get('uri')

        request_url = f"{args.url}/api/storage/{args.repository}/{root_path}{uri}?properties"

        artifact_properties = {}

        try:
            props_response = api_request(
                "get", request_url, args.user, args.password, args.apikey)
            artifact_properties = json.loads(props_response).get("properties")
        except:
            pass

        for property in args.property:
            key, val = property.split('=')[0], property.split('=')[1]
            if artifact_properties.get(key) and val not in artifact_properties.get(key):
                artifact_properties[key].append(val)
            else:
                artifact_properties[key] = val

        if artifact_properties:
            request_url = f"{args.url}/api/metadata/{args.repository}/{root_path}{uri}?&recursiveProperties=0"
            api_request("patch", request_url, args.user, args.password,
                        args.apikey, json_data=json.dumps({"props": artifact_properties}))


@conan_subcommand()
def property_set(conan_api: ConanAPI, parser, subparser, *args):
    """
    Set properties for artifacts under a Conan reference recursively.
    """

    add_default_arguments(subparser)

    subparser.add_argument('--no-recursive', dest='recursive',
                           action='store_false', help='Will not recursively set properties.')
    args = parser.parse_args(*args)

    recursive = "1" if args.recursive else "0"

    json_data = json.dumps(
        {"props": {prop.split('=')[0]: prop.split('=')[1] for prop in args.property}})

    request_url = f"{args.url}/api/metadata/{args.repository}/{get_path_from_ref(args.reference)}?&recursiveProperties={recursive}"

    api_request("patch", request_url, args.user, args.password, args.apikey, json_data=json_data)


@conan_subcommand()
def property_build_info_add(conan_api: ConanAPI, parser, subparser, *args):
    """
    Load a Build Info JSON and add the build.number and build.name properties to all the artifacts present in the JSON.
    """

    subparser.add_argument("json", help="Build Info JSON.")
    subparser.add_argument("url", help="Artifactory url, like: https://<address>/artifactory")

    subparser.add_argument("--user", help="user name for the repository")
    subparser.add_argument("--password", help="password for the user name")
    subparser.add_argument("--apikey", help="apikey for the repository")

    args = parser.parse_args(*args)

    with open(args.json, 'r') as f:
        data = json.load(f)

    build_name = data.get("name")
    build_number = data.get("number")

    for module in data.get('modules'):
        for artifact in module.get('artifacts'):
            artifact_properties = {}
            artifact_path = artifact.get('path')
            try:
                request_url = f"{args.url}/api/storage/{artifact_path}?properties"
                props_response = api_request("get", request_url, args.user, args.password, args.apikey)
                artifact_properties = json.loads(props_response).get("properties")
            except:
                pass

            if artifact_properties.get("build.name") and build_name not in artifact_properties.get("build.name"):
                artifact_properties["build.name"].append(build_name)
            else:
                artifact_properties["build.name"] = build_name

            if artifact_properties.get("build.number") and build_number not in artifact_properties.get("build.number"):
                artifact_properties["build.number"].append(build_number)
            else:
                artifact_properties["build.number"] = build_number
        

            request_url = f"{args.url}/api/metadata/{artifact_path}"
            api_request("patch", request_url, args.user, args.password,
                        args.apikey, json_data=json.dumps({"props": artifact_properties}))
