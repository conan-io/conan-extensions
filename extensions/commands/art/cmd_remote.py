import base64
import getpass
import json
import os.path
import requests

from conan.api.conan_api import ConanAPI
from conan.api.output import ConanOutput, cli_out_write
from conan.cli.command import conan_command, conan_subcommand
from conan.errors import ConanException

REMOTES_FILE = "art-remote.conf"


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
        raise ConanException(response_to_str(response))
    elif response.status_code not in [200, 204]:
        raise ConanException(response_to_str(response))

    return response_to_str(response)


def read_remotes():
    path = os.path.join(os.path.dirname(__file__), REMOTES_FILE)
    remotes = []
    if os.path.exists(path):
        with open(path) as remotes_file:
            data_encoded = remotes_file.read()
            data = base64.b64decode(data_encoded).decode('utf-8')
            remotes_data = json.loads(data)
            remotes = remotes_data["remotes"]
    return remotes


def write_remotes(remotes):
    path = os.path.join(os.path.dirname(__file__), REMOTES_FILE)
    with open(path, "w") as remotes_file:
        data = json.dumps({"remotes": remotes})
        remotes_file.write(base64.b64encode(data.encode('utf-8')).decode('utf-8'))


def assert_new_remote(remote_name, remotes):
    for r in remotes:
        if remote_name == r["name"]:
            raise ConanException(f"Remote '{remote_name}' ({r['url']}) already exist. "
                                 f"You can remove it using `conan art:remote remove {remote_name}`")


def assert_existing_remote(remote_name, remotes):
    remote_names = [r["name"] for r in remotes]
    if remote_name not in remote_names:
        raise ConanException(f"Remote '{remote_name}' does not exist.")


def add_default_arguments(subparser):
    subparser.add_argument("name", help="Name of the remote")
    return subparser


@conan_command(group="Custom commands")
def remote(conan_api: ConanAPI, parser, *args):
    """
    Manages Artifactory server and credentials.
    """


@conan_subcommand()
def remote_add(conan_api: ConanAPI, parser, subparser, *args):
    """
    Add Artifactory remote and its credentials.
    """
    add_default_arguments(subparser)
    subparser.add_argument("artifactory_url", help="URL of the artifactory server")
    subparser.add_argument("--user", help="user name for the repository")
    subparser.add_argument("--password", help="password for the user name")

    args = parser.parse_args(*args)

    if not args.user:
        user = input("User: ")
    else:
        user = args.user.strip()
    if not args.password:
        password = getpass.getpass()
    else:
        password = args.password.strip()

    name = args.name.strip()
    artifactory_url = args.artifactory_url.rstrip("/")

    remotes = read_remotes()
    assert_new_remote(name, remotes)

    token = api_request("get", f"{artifactory_url}/api/security/encryptedPassword", user, password)
    # TODO: manage error with auth

    new_remote = {"name": name,
                  "url": artifactory_url,
                  "user": user,
                  "password": token}
    remotes.append(new_remote)
    write_remotes(remotes)
    ConanOutput().success(f"Remote '{name}' ({artifactory_url}) added successfully")


@conan_subcommand()
def remote_remove(conan_api: ConanAPI, parser, subparser, *args):
    """
    Remove Artifactory remotes.
    """
    add_default_arguments(subparser)
    args = parser.parse_args(*args)

    name = args.name.strip()
    remotes = read_remotes()
    assert_existing_remote(name, remotes)
    artifactory_url = None
    keep_remotes = []
    for r in remotes:
        if name != r["name"]:
            keep_remotes.append(r)
        else:
            artifactory_url = r["url"]
    write_remotes(keep_remotes)
    ConanOutput().success(f"Remote '{name}' ({artifactory_url}) removed successfully")


def output_remote_list_cli(remotes):
    if remotes:
        for r in remotes:
            ConanOutput().info(f"{r['name']}:")
            ConanOutput().info(f"  url: {r['url']}")
            ConanOutput().info(f"  user: {r['user']}")
            ConanOutput().info(f"  password: *******")
    else:
        ConanOutput().info("No remotes configured. Use `conan art:remote add` command to add one.")


def output_remote_list_json(servers):
    result = []
    for s in servers:
        s["password"] = "*******"
        result.append(s)
    cli_out_write(json.dumps({"remotes": result}, indent=4))


@conan_subcommand(formatters={"cli": output_remote_list_cli,
                              "json": output_remote_list_json})
def remote_list(conan_api: ConanAPI, parser, subparser, *args):
    """
    List Artifactory remotes.
    """
    return read_remotes()
