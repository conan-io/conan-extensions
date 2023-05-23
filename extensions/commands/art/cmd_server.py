import base64
import getpass
import json
import os.path
import requests

from conan.api.conan_api import ConanAPI
from conan.api.output import ConanOutput, cli_out_write
from conan.cli.command import conan_command, conan_subcommand
from conan.errors import ConanException

SERVERS_FILENAME = ".art-servers"


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


def read_servers():
    path = os.path.join(os.path.dirname(__file__), SERVERS_FILENAME)
    servers = []
    if os.path.exists(path):
        with open(path) as servers_file:
            data_encoded = servers_file.read()
            data = base64.b64decode(data_encoded).decode('utf-8')
            servers_data = json.loads(data)
            servers = servers_data["servers"]
    return servers


def write_servers(servers):
    path = os.path.join(os.path.dirname(__file__), SERVERS_FILENAME)
    with open(path, "w") as servers_file:
        data = json.dumps({"servers": servers})
        servers_file.write(base64.b64encode(data.encode('utf-8')).decode('utf-8'))


def assert_new_server(server_name, servers):
    for s in servers:
        if server_name == s["name"]:
            raise ConanException(f"Server '{server_name}' ({s['url']}) already exist. "
                                 f"You can remove it using `conan art:server remove {server_name}`")


def assert_existing_server(server_name, servers):
    server_names = [s["name"] for s in servers]
    if server_name not in server_names:
        raise ConanException(f"Server '{server_name}' does not exist.")


def add_default_arguments(subparser):
    subparser.add_argument("name", help="Name of the server")
    return subparser


@conan_command(group="Custom commands")
def server(conan_api: ConanAPI, parser, *args):
    """
    Manages Artifactory server and credentials.
    """


@conan_subcommand()
def server_add(conan_api: ConanAPI, parser, subparser, *args):
    """
    Add Artifactory server and its credentials.
    """
    add_default_arguments(subparser)
    subparser.add_argument("url", help="URL of the artifactory server")
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
    url = args.url.rstrip("/")

    servers = read_servers()
    assert_new_server(name, servers)

    token = api_request("get", f"{url}/api/security/encryptedPassword", user, password)
    # TODO: manage error with auth

    new_server = {"name": name,
                  "url": url,
                  "user": user,
                  "password": token}
    servers.append(new_server)
    write_servers(servers)
    ConanOutput().success(f"Server '{name}' ({url}) added successfully")


@conan_subcommand()
def server_remove(conan_api: ConanAPI, parser, subparser, *args):
    """
    Remove Artifactory servers.
    """
    add_default_arguments(subparser)
    args = parser.parse_args(*args)

    name = args.name.strip()
    servers = read_servers()
    assert_existing_server(name, servers)
    url = None
    keep_servers = []
    for s in servers:
        if name != s["name"]:
            keep_servers.append(s)
        else:
            url = s["url"]
    write_servers(keep_servers)
    ConanOutput().success(f"Server '{name}' ({url}) removed successfully")


def output_server_list_text(servers):
    if servers:
        for s in servers:
            cli_out_write(f"{s['name']}:")
            cli_out_write(f"url: {s['url']}", indentation=2)
            cli_out_write(f"user: {s['user']}", indentation=2)
            cli_out_write(f"password: *******", indentation=2)
    else:
        cli_out_write("No servers configured. Use `conan art:server add` command to add one.")


def output_server_list_json(servers):
    [s.pop("password") for s in servers]
    cli_out_write(json.dumps({"servers": servers}, indent=4))


@conan_subcommand(formatters={"text": output_server_list_text,
                              "json": output_server_list_json})
def server_list(conan_api: ConanAPI, parser, subparser, *args):
    """
    List Artifactory servers.
    """
    return read_servers()
