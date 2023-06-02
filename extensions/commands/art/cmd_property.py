import json

from conan.api.conan_api import ConanAPI
from conan.cli.command import conan_command, conan_subcommand
from conans.model.recipe_ref import RecipeReference
from conans.model.package_ref import PkgReference
from conan.errors import ConanException

from utils import api_request, assert_server_or_url_user_password
from cmd_server import get_url_user_password


def set_properties(properties, path, url, user, password, recursive):
    json_data = json.dumps({"props": properties})
    recursive = "1" if recursive else "0"
    request_url = f"{url}/api/metadata/{path}?&recursiveProperties={recursive}"
    api_request("patch", request_url, user, password, json_data=json_data)


def get_properties(path, url, user, password):
    properties = {}
    request_url = f"{url}/api/storage/{path}?properties"

    try:
        props_response = api_request("get", request_url, user, password)
        properties = json.loads(props_response).get("properties")
    except:
        pass
    return properties


def _get_path_from_ref(ref):
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


def _add_default_arguments(subparser):
    subparser.add_argument("repository", help="Artifactory repository.")
    subparser.add_argument("reference", help="Conan reference.")
    subparser.add_argument("--server", help="Server name of the Artifactory to get the build info from")
    subparser.add_argument("--url", help="Artifactory url, like: https://<address>/artifactory")
    subparser.add_argument("--user", help="user name for the repository")
    subparser.add_argument("--password", help="password for the user name")
    subparser.add_argument("--property", action='append',
                           help='Property to add, like --property="build.name=buildname" --property="build.number=1"')

    return subparser


@conan_command(group="Artifactory commands")
def property(conan_api: ConanAPI, parser, *args):
    """
    Manages Conan packages properties in Artifactory.
    """


@conan_subcommand()
def property_add(conan_api: ConanAPI, parser, subparser, *args):
    """
    Append properties for artifacts under a Conan reference recursively.
    """

    _add_default_arguments(subparser)

    args = parser.parse_args(*args)

    assert_server_or_url_user_password(args)

    if not args.property:
        raise ConanException("Please, add at least one property with the --property argument.")

    # TODO: do we want to add properties to folders? it's slower but when
    # we set properties recursive the folders are also set, so setting also
    # for folders for consistency and check what to do
    list_folders = "1"

    # get artifacts recursively from a starting path
    root_path = _get_path_from_ref(args.reference)

    url, user, password = get_url_user_password(args)

    request_url = f"{url}/api/storage/{args.repository}/{root_path}?list&deep=1&listFolders={list_folders}"

    data = json.loads(api_request("get", request_url, user, password))


    # just consider those artifacts that have conan in the name
    # conan_artifacts = [artifact for artifact in data.get("files") if "conan" in artifact.get('uri')]

    # get properties for all artifacts
    for artifact in data.get("files"):
        uri = artifact.get('uri')
        path = f"{args.repository}/{root_path}{uri}"

        artifact_properties = get_properties(path, url, user, password)

        for property in args.property:
            key, val = property.split('=')[0], property.split('=')[1]
            artifact_properties.setdefault(key, []).append(val)

        if artifact_properties:
            set_properties(artifact_properties, path, url, user, password, False)


@conan_subcommand()
def property_set(conan_api: ConanAPI, parser, subparser, *args):
    """
    Set properties for artifacts under a Conan reference.
    """

    _add_default_arguments(subparser)

    subparser.add_argument('--no-recursive', dest='recursive',
                           action='store_false', help='Will not recursively set properties.')
    args = parser.parse_args(*args)
    assert_server_or_url_user_password(args)

    if not args.property:
        raise ConanException("Please, add at least one property with the --property argument.")

    # json_data = json.dumps(
    #     {"props": {prop.split('=')[0]: prop.split('=')[1] for prop in args.property}})
    properties = {prop.split('=')[0]: prop.split('=')[1] for prop in args.property}
    path = f"{args.repository}/{_get_path_from_ref(args.reference)}"
    url, user, password = get_url_user_password(args)
    recursive = "1" if args.recursive else "0"

    set_properties(properties, path, url, user, password, recursive)
