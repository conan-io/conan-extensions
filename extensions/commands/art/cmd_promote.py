import json
import os.path

from conan.api.conan_api import ConanAPI
from conan.api.output import ConanOutput
from conan.cli.command import conan_command
try:
    from conan.api.model import RecipeReference, PkgReference
except:
    from conans.model.recipe_ref import RecipeReference
    from conans.model.package_ref import PkgReference
from conan.api.model import MultiPackagesList
from conan.errors import ConanException

from utils import api_request, assert_server_or_url_user_password
from cmd_server import get_url_user_password


def _get_export_path_from_rrev(rrev):
    recipe_ref = RecipeReference.loads(rrev)
    user = recipe_ref.user or "_"
    channel = recipe_ref.channel or "_"
    path = f"{user}/{recipe_ref.name}/{recipe_ref.version}/{channel}"
    if recipe_ref.revision:
        path += f"/{recipe_ref.revision}/export/"
    return path


def _get_path_from_pref(pref):
    package_ref = PkgReference.loads(pref)
    recipe_ref = package_ref.ref

    user = recipe_ref.user or "_"
    channel = recipe_ref.channel or "_"

    path = f"{user}/{recipe_ref.name}/{recipe_ref.version}/{channel}/{recipe_ref.revision}/package/{package_ref.package_id}"
    if package_ref.revision:
        path += f"/{package_ref.revision}"
    return path


def _request(url, user, password, request_type, request_url):
    try:
        return json.loads(api_request(request_type, f"{url}{request_url}", user, password))
    except Exception as e:
        raise ConanException(f"Error requesting {request_url}: {e}")


def _promote_path(url, user, password, origin, destination, path):
    ConanOutput().subtitle(f"Promoting {path}")
    # The copy api creates a subfolder if the destination already exists, need to check beforehand to avoid this
    try:
        # This first request will raise a 404 if no file is found
        _request(url, user, password, "get", f"api/storage/{destination}/{path}")
        ConanOutput().warning("Destination already exists, skipping")
    except ConanException:
        _request(url, user, password, "post", f"api/copy/{origin}/{path}?to=/{destination}/{path}&suppressLayouts=0")
        ConanOutput().success("Promoted file")


@conan_command(group="Artifactory")
def promote(conan_api: ConanAPI, parser, *args):
    """
    Promote Conan recipes and packages in a pkglist file from an origin Artifactory repository to a destination repository, without downloading the packages locally
    """

    parser.add_argument("list", help="Package list file to promote")
    parser.add_argument("--from", help="Artifactory origin repository name", required=True, dest="origin")
    parser.add_argument("--to", help="Artifactory destination repository name", required=True, dest="destination")

    parser.add_argument("--remote", help="Promote packages from this remote (to disambiguate in case of packages from different repos)", default=None)

    parser.add_argument("--server", help="Server name of the Artifactory server to promote from if using art:property commands")
    parser.add_argument("--url", help="Artifactory server url, like: https://<address>/artifactory")
    parser.add_argument("--user", help="User name for the repository")
    parser.add_argument("--password", help="Password for the user name (instead of token)")
    parser.add_argument("--token", help="Token for the repository (instead of password)")

    args = parser.parse_args(*args)

    url, user, password = get_url_user_password(args)
    if not url.endswith("/"):
        url += "/"

    listfile = os.path.realpath(args.list)
    multi_package_list = MultiPackagesList.load(listfile)

    remotes = list(multi_package_list.lists.keys())
    if len(remotes) > 1 and args.remote is None:
        raise ConanException(f"Expected every package to come from the same origin repository in {args.origin}, "
                             f"use --remote to disambiguate")

    if args.remote is not None:
        origin_remote = args.remote
        if origin_remote not in remotes:
            raise ConanException(f"Remote {origin_remote} not found in the package list")
    else:
        origin_remote = remotes[0]

    if origin_remote == "Local Cache":
        raise ConanException(f"Package list must come from the remote associated with {args.origin}, "
                             f"but found from local cache")

    assert_server_or_url_user_password(args)

    # Only artifactory pro edition supports this feature
    response = _request(url, user, password, "get", "api/system/version")
    if response["license"] == "Artifactory Community Edition for C/C++":
        raise ConanException("Direct graph promotion is only supported in Artifactory Pro. "
                             "As an alternative, use conan download + conan upload with the pkglist feature")

    pkglist = multi_package_list[origin_remote]

    for name_version, recipe in pkglist.serialize().items():
        if "revisions" not in recipe:
            ConanOutput().info(f"Recipe {name_version} does not have a revision, skipping")
            continue
        for rrev, recipe_revision in recipe["revisions"].items():
            _promote_path(url, user, password, args.origin, args.destination, _get_export_path_from_rrev(f"{name_version}#{rrev}"))
            if "packages" not in recipe_revision:
                ConanOutput().info(f"Recipe {name_version}#{rrev} does not have any package, skipping")
                continue
            for pkgid, package in recipe_revision["packages"].items():
                if "revisions" not in package:
                    _promote_path(url, user, password, args.origin, args.destination,
                                  _get_path_from_pref(f"{name_version}#{rrev}:{pkgid}"))
                    ConanOutput().info(f"Package {name_version}#{rrev}:{pkgid} does not have explicit revisions, skipping")
                else:
                    for prev, package_revision in package["revisions"].items():
                        _promote_path(url, user, password, args.origin, args.destination, _get_path_from_pref(f"{name_version}#{rrev}:{pkgid}#{prev}"))
