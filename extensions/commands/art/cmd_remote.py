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
    subparser.add_argument("name", help="Name of the remote to add")
    return subparser


@conan_command(group="Custom commands")
def remote(conan_api: ConanAPI, parser, *args):
    """
    Manages Artifactory server and credentials.
    """


@conan_subcommand()
def remote_add(conan_api: ConanAPI, parser, subparser, *args):
    """
    Add Artifactory server with crendentials to configuration.
    """
    add_default_arguments(subparser)
    subparser.add_argument("artifactory_url", help="URL of the artifactory server")
    subparser.add_argument("--user", help="user name for the repository")
    subparser.add_argument("--password", help="password for the user name")

    args = parser.parse_args(*args)

    artifactory_url = args.artifactory_url.rstrip("/")

    if not args.user or not args.password:
        raise ConanException(f"User and password are required to authenticate ({artifactory_url}).")

    name = args.name.strip()
    artifactory_url = args.artifactory_url.rstrip("/")
    user = args.user.strip()
    password = args.password.strip()

    #read json file
    #check remote name already exist --> raise error

    token = api_request("get", f"{artifactory_url}/api/security/encryptedPassword", user, password)

    #manage error with auth
    #save to json file

    remote_registry = {"name": name, "artifactory_url": artifactory_url, "user": user, "password": token}
    print(remote_registry)

@conan_subcommand()
def remote_remove(conan_api: ConanAPI, parser, subparser, *args):
    """
    Remove Artifactory server from configuration.
    """
    add_default_arguments(subparser)
    args = parser.parse_args(*args)

    remote = args.remote

    #read from json file
    #manage error reading
    #check remote provided exist in file
    #remove remote
    #savefile
    #manage error saving the file