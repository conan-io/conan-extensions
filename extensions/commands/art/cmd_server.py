import base64
import getpass
import json
import os.path

from conan.api.conan_api import ConanAPI
from conan.api.output import ConanOutput, cli_out_write
from conan.cli.command import conan_command, conan_subcommand
from conan.errors import ConanException

from utils import api_request

SERVERS_FILENAME = ".art-servers"


def get_url_user_password(args):
    if args.server:
        server_name = args.server.strip()
        server = _get_server(server_name)
        url = server.get("url")
        user = server.get("user")
        password = server.get("password")
    else:
        url = args.url
        user = args.user
        password = args.password or args.token
    return url, user, password


def _get_server(server_name):
    servers = _read_servers()
    server_names = [s["name"] for s in servers]
    if server_name not in server_names:
        raise ConanException(f"The server specified ({server_name}) is not configured. "
                             f"Use `conan art:server add {server_name}` to configure it.")
    for s in servers:
        if s["name"] == server_name:
            return s


def _read_servers():
    path = os.path.join(os.path.dirname(__file__), SERVERS_FILENAME)
    servers = []
    if os.path.exists(path):
        with open(path) as servers_file:
            data_encoded = servers_file.read()
            data = base64.b64decode(data_encoded).decode('utf-8')
            servers_data = json.loads(data)
            servers = servers_data["servers"]
    return servers


def _write_servers(servers):
    path = os.path.join(os.path.dirname(__file__), SERVERS_FILENAME)
    with open(path, "w") as servers_file:
        data = json.dumps({"servers": servers})
        servers_file.write(base64.b64encode(data.encode('utf-8')).decode('utf-8'))


def _assert_new_server(server_name, servers):
    for s in servers:
        if server_name == s["name"]:
            raise ConanException(f"Server '{server_name}' ({s['url']}) already exist. "
                                 f"You can remove it using `conan art:server remove {server_name}`")


def _assert_existing_server(server_name, servers):
    server_names = [s["name"] for s in servers]
    if server_name not in server_names:
        raise ConanException(f"Server '{server_name}' does not exist.")


def _add_default_arguments(subparser):
    subparser.add_argument("name", help="Name of the server")
    return subparser


@conan_command(group="Artifactory")
def server(conan_api: ConanAPI, parser, *args):
    """
    Manages Artifactory server and credentials.
    """


@conan_subcommand()
def server_add(conan_api: ConanAPI, parser, subparser, *args):
    """
    Add Artifactory server and its credentials.
    """
    _add_default_arguments(subparser)
    subparser.add_argument("url", help="URL of the artifactory server")
    subparser.add_argument("--user", help="user name for the repository")
    subparser.add_argument("--password", help="password for the user name")
    subparser.add_argument("--token", help="Token for the artifactory server")

    args = parser.parse_args(*args)

    token = None

    if not args.user:
        user = input("User: ")
    else:
        user = args.user.strip()
    if args.token:
        token = args.token.strip()
    else:
        if not args.password:
            password = getpass.getpass()
        else:
            password = args.password.strip()

    name = args.name.strip()
    url = args.url.rstrip("/")

    servers = _read_servers()
    _assert_new_server(name, servers)

    if not token:
        # TODO: manage error with auth
        token = api_request("get", f"{url}/api/security/encryptedPassword", user, password)

    # Check token is valid
    api_request("get", f"{url}/api/v1/system/ping", user, token)

    new_server = {"name": name,
                  "url": url,
                  "user": user,
                  "password": token}
    servers.append(new_server)
    _write_servers(servers)
    ConanOutput().success(f"Server '{name}' ({url}) added successfully")


@conan_subcommand()
def server_remove(conan_api: ConanAPI, parser, subparser, *args):
    """
    Remove Artifactory servers.
    """
    _add_default_arguments(subparser)
    args = parser.parse_args(*args)

    name = args.name.strip()
    servers = _read_servers()
    _assert_existing_server(name, servers)
    url = None
    keep_servers = []
    for s in servers:
        if name != s["name"]:
            keep_servers.append(s)
        else:
            url = s["url"]
    _write_servers(keep_servers)
    ConanOutput().success(f"Server '{name}' ({url}) removed successfully")


def _output_server_list_text(servers):
    if servers:
        for s in servers:
            cli_out_write(f"{s['name']}:")
            cli_out_write(f"url: {s['url']}", indentation=2)
            cli_out_write(f"user: {s['user']}", indentation=2)
            cli_out_write(f"password: *******", indentation=2)
    else:
        cli_out_write("No servers configured. Use `conan art:server add` command to add one.")


def _output_server_list_json(servers):
    [s.pop("password") for s in servers]
    cli_out_write(json.dumps({"servers": servers}, indent=4))


@conan_subcommand(formatters={"text": _output_server_list_text,
                              "json": _output_server_list_json})
def server_list(conan_api: ConanAPI, parser, subparser, *args):
    """
    List Artifactory servers.
    """
    return _read_servers()
