import json
import os.path
import urllib.parse
import requests

from conan.api.conan_api import ConanAPI
from conan.api.model import MultiPackagesList, PkgReference, RecipeReference
from conan.api.output import ConanOutput
from conan.cli.command import conan_command
from conan.errors import ConanException
from utils import api_request, assert_server_or_url_user_password, NotFoundException
from cmd_server import get_url_user_password

# All the requests share this session, so they reuse the connection to the server instead of opening a new one
# (TCP and TLS handshakes) for each of them, which is most of the time of a request
_session = requests.Session()


def _get_export_path_from_rrev(rrev):
    recipe_ref = RecipeReference.loads(rrev)
    user = recipe_ref.user or "_"
    channel = recipe_ref.channel or "_"
    path = f"{user}/{recipe_ref.name}/{recipe_ref.version}/{channel}"
    if recipe_ref.revision:
        path += f"/{recipe_ref.revision}/export"
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
        return json.loads(api_request(request_type, f"{url}{request_url}", user, password,
                                      session=_session))
    except ConanException:
        raise
    except Exception as e:
        raise ConanException(f"Error requesting {request_url}: {e}")


def _list_folder(url, user, password, repo, folder):
    """ Files in the folder of the repository (recursively), as a set of paths relative to the folder,
    like "/conanfile.py" or "/metadata/logs/build.txt"

    Raises NotFoundException if the folder does not exist
    """
    storage_list = _request(url, user, password, "get", f"api/storage/{repo}/{folder}?list&deep=1")
    return {item["uri"] for item in storage_list.get("files", [])}


def _list_origin_folder(url, user, password, origin, folder, ref):
    try:
        return _list_folder(url, user, password, origin, folder)
    except NotFoundException:
        raise ConanException(f"{ref} not found in the '{origin}' repository, cannot promote. "
                             f"Make sure it exists in the origin repository.")


def _check_complete(files, required, ref, origin):
    missing = [file[1:] for file in required if file not in files]
    if missing:
        raise ConanException(f"{ref} is missing {', '.join(missing)} in the '{origin}' repository, "
                             f"cannot promote. Make sure it exists and is complete in the origin repository.")


def _metadata_files(files):
    return sorted(file for file in files if file.startswith("/metadata/"))


def _compressed_files(files, names):
    """ For each name, the compressed file (like conan_package.tgz) with the compression it was uploaded with """
    compressed = []
    for name in names:
        for ext in ["tgz", "tzst", "txz"]:
            if f"{name}.{ext}" in files:
                compressed.append(f"{name}.{ext}")
                break
    return compressed


def _promote_path(url, user, password, origin, destination, path, exists, force):
    """ Promote path from origin to destination, unless it already exists in the destination
    and force is not set. exists tells if the path is already in the destination

    Raises if the promotion fails (the file is not there after calling this)
    """
    ConanOutput().subtitle(f"Promoting {path}")
    if exists:
        if not force:
            ConanOutput().info("Destination already exists, skipping")
            return
        ConanOutput().info("Destination already exists, overwriting (--force)")

    path = urllib.parse.quote_plus(path, safe='/')
    try:
        _request(url, user, password, "post",
                 f"api/copy/{origin}/{path}?to=/{destination}/{path}&suppressLayouts=0")
    except ConanException as e:
        ConanOutput().error(f"Failed to promote {path}: {e}")
        raise
    ConanOutput().success("Promoted file")


def _list_destination_folder(url, user, password, destination, folder):
    """ Files in the folder of the destination repository, None if the folder does not exist yet """
    try:
        return _list_folder(url, user, password, destination, folder)
    except NotFoundException:
        return None
    except ConanException as e:
        ConanOutput().error(f"Failed to list '{folder}' in the '{destination}' repository: {e}")
        raise


def _promote_files(url, user, password, origin, destination, folder, files, destination_files, force):
    """ Promote the files (paths relative to the folder), in order, from origin to destination.

    destination_files are the files that are already in the destination folder (listed only once by the caller)
    """
    for file in files:
        _promote_path(url, user, password, origin, destination, f"{folder}{file}",
                      exists=file in destination_files, force=force)


def _promote_recipe_folder(url, user, password, origin, destination, folder):
    """ Promote the whole folder of a recipe revision at once, with a single copy.

    The copy cannot be merged into a folder that already exists, Artifactory creates a subfolder
    inside of it, so the folder must not exist in the destination
    """
    _promote_path(url, user, password, origin, destination, f"{folder}/", exists=False, force=False)


def _promote_recipe_rrev(url, user, password, origin, destination, rrev, force=False):
    folder = _get_export_path_from_rrev(rrev)
    ref = f"Recipe {rrev}"
    files = _list_origin_folder(url, user, password, origin, folder, ref)

    # Ensure we have a valid Conan recipe
    info_files = ["/conanfile.py", "/conanmanifest.txt"]
    _check_complete(files, info_files, ref, origin)

    destination_files = _list_destination_folder(url, user, password, destination, folder)
    if destination_files is None:
        # The recipe revision is not in the destination yet, so it is promoted all at once, with a single copy
        _promote_recipe_folder(url, user, password, origin, destination, folder)
    else:
        # The files that make the recipe valid go last
        to_promote = (_metadata_files(files)
                      + _compressed_files(files, ["/conan_export", "/conan_sources"])
                      + info_files)
        _promote_files(url, user, password, origin, destination, folder, to_promote, destination_files, force)


def _promote_package_prev(url, user, password, origin, destination, pref_with_prev, force=False):
    # We need to manually promote the files one by one, else Artifactory's
    # automatic .timestamp handling would create overwrites.
    # We let Artifactory handle the .timestamp copy
    # which allows this command to be executed without overwrite permissions
    # (unless --force is used, as that overwrites the files that already exist)
    folder = _get_path_from_pref(pref_with_prev)
    ref = f"Package {pref_with_prev}"
    files = _list_origin_folder(url, user, password, origin, folder, ref)

    # Ensure we have a valid Conan package
    info_files = ["/conaninfo.txt", "/conanmanifest.txt"]
    _check_complete(files, info_files, ref, origin)

    # The files that make the package valid go last
    to_promote = (_compressed_files(files, ["/conan_package"])
                  + _metadata_files(files)
                  + info_files)
    destination_files = _list_destination_folder(url, user, password, destination, folder) or set()
    _promote_files(url, user, password, origin, destination, folder, to_promote, destination_files, force)


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

    parser.add_argument("--force", help="Overwrite the files that already exist in the destination repository, "
                                        "instead of skipping them. Needs overwrite permissions in the destination "
                                        "repository", action="store_true")

    args = parser.parse_args(*args)

    assert_server_or_url_user_password(args)
    url, user, password = get_url_user_password(args)
    if not url.endswith("/"):
        url += "/"

    listfile = os.path.realpath(args.list)
    multi_package_list = MultiPackagesList.load(listfile)

    remotes = list(multi_package_list.lists.keys())
    if len(remotes) > 1 and args.remote is None:
        raise ConanException(f"Expected every package to come from the same origin repository in {args.origin}, "
                             f"use --remote to disambiguate")
    if len(remotes) == 0:
        ConanOutput().info(f"Nothing to promote, empty package list {args.list}")
        return

    if args.remote is not None:
        origin_remote = args.remote
        if origin_remote not in remotes:
            raise ConanException(f"Remote {origin_remote} not found in the package list")
    else:
        origin_remote = remotes[0]

    if origin_remote == "Local Cache":
        raise ConanException(f"Package list must come from the remote associated with {args.origin}, "
                             f"but found from local cache")

    # Only artifactory pro edition supports this feature
    response = _request(url, user, password, "get", "api/system/version")
    if response["license"] == "Artifactory Community Edition for C/C++":
        raise ConanException("Direct graph promotion is only supported in Artifactory Pro. "
                             "As an alternative, use conan download + conan upload with the pkglist feature")

    pkglist = multi_package_list[origin_remote]

    for name_version, recipe in pkglist.serialize().items():
        if "revisions" not in recipe:
            raise ConanException(f"Recipe {name_version} does not have any revisions specified. "
                                 "It's necessary to specify recipe revisions for promotion.")
        for rrev, recipe_revision in recipe["revisions"].items():
            _promote_recipe_rrev(url, user, password, args.origin, args.destination,
                                 f"{name_version}#{rrev}", force=args.force)
            if "packages" not in recipe_revision:
                ConanOutput().info(f"Recipe {name_version}#{rrev} does not have any package, skipping")
                continue
            for pkgid, package in recipe_revision["packages"].items():
                if "revisions" not in package:
                    raise ConanException(f"Package {name_version}#{rrev}:{pkgid} does not have any revisions specified. "
                                         "It's necessary to specify package revisions for promotion.")
                for prev, package_revision in package["revisions"].items():
                    _promote_package_prev(url, user, password,
                                          args.origin, args.destination,
                                          f"{name_version}#{rrev}:{pkgid}#{prev}",
                                          force=args.force)
