import json
import os

from conan.api.conan_api import ConanAPI
from conan.api.output import cli_out_write
from conan.cli.command import conan_command, conan_subcommand

from utils import api_request, assert_server_or_url_user_password
from cmd_server import get_url_user_password


def upload_file(repository, file, upload_path, url, user, password):
    filename = os.path.basename(file)

    request_url = f"{url}/{repository}/{upload_path}/{filename}"
    file_content = _read_file(file)

    return api_request("put", request_url, user, password, json_data=file_content)

def read_file(repository, file, url, user, password):
    request_url = f"{url}/{repository}/{file}"
    file_content = api_request("get", request_url, user, password)
    return file_content

def list_folders(repository, path, url, user, password):
    request_url = f"{url}/api/storage/{repository}/{path}"
    response = json.loads(api_request("get", request_url, user, password))
    print(response)
    folders = [item["uri"] for item in response["children"] if item["folder"]]
    return folders


def _read_file(path):
    if os.path.exists(path):
        with open(path) as file:
            data = file.read()
            return data


def _add_default_arguments(subparser):
    subparser.add_argument("repository", help="Artifactory repository.")
    subparser.add_argument("--server", help="Server name of the Artifactory to get the build info from")
    subparser.add_argument("--url", help="Artifactory url, like: https://<address>/artifactory")
    subparser.add_argument("--user", help="user name for the repository")
    subparser.add_argument("--password", help="password for the user name")
    return subparser


@conan_command(group="Artifactory")
def generic_repo(conan_api: ConanAPI, parser, *args):
    """
    Manages files of Generic repositories in Artifactory.
    """


@conan_subcommand()
def generic_repo_upload(conan_api: ConanAPI, parser, subparser, *args):
    """
    Upload file to a Generic repository
    """

    _add_default_arguments(subparser)
    subparser.add_argument("file", help="File to be uploaded")
    subparser.add_argument("upload_path", help="Folder path to store the file in the generic repo")

    args = parser.parse_args(*args)

    assert_server_or_url_user_password(args)

    url, user, password = get_url_user_password(args)
    response = upload_file(args.repository, args.file, args.upload_path, url, user, password)
    cli_out_write(response)


@conan_subcommand()
def generic_repo_read(conan_api: ConanAPI, parser, subparser, *args):
    """
    Read content from a file in a Generic repository
    """

    _add_default_arguments(subparser)
    subparser.add_argument("file", help="File to be read from repository")

    args = parser.parse_args(*args)

    assert_server_or_url_user_password(args)

    url, user, password = get_url_user_password(args)

    file_content = read_file(args.repository, args.file, url, user, password)
    cli_out_write(file_content)


@conan_subcommand()
def generic_repo_list(conan_api: ConanAPI, parser, subparser, *args):
    """
    List content from a folder Generic repository
    """

    _add_default_arguments(subparser)
    subparser.add_argument("path", help="File to be read from repository")

    args = parser.parse_args(*args)

    assert_server_or_url_user_password(args)

    url, user, password = get_url_user_password(args)

    folders = list_folders(args.repository, args.path, url, user, password)
    cli_out_write(json.dumps(folders))
