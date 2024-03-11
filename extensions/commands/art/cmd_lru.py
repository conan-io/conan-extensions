import json

from conan.api.conan_api import ConanAPI
from conan.api.model import ListPattern
from conan.api.output import ConanOutput
from conan.cli.command import conan_command, conan_subcommand
from conan.internal.conan_app import ConanApp
from conans.errors import ConanException
from conans.model.package_ref import PkgReference
from conans.util.dates import timelimit

from cmd_server import get_url_user_password
from utils import api_request


@conan_command(group="Artifactory")
def lru(conan_api: ConanAPI, parser, *args):
    """
    Interacts with LRU information of Conan packages in Artifactory
    """


@conan_subcommand()
def lru_remove(conan_api: ConanAPI, parser, subparser, *args):
    """
    Remove Conan packages not downloaded in X amount of time
    """

    # _add_default_arguments(subparser)
    subparser.add_argument('remote',
                           help="Artifactory remote to remove from")
    subparser.add_argument('pattern',
                           help="Selection pattern for references to clean")
    subparser.add_argument('lru',
                           help="Remove recipes and binaries that have not been recently used. Use a"
                                " time limit like 5d (days) or 4w (weeks), h (hours) or m(minutes)")

    subparser.add_argument('--dry-run', default=False, action="store_true",
                           help="Don't remove, just list what would be removed")
    subparser.add_argument("--server",
                           help="Server name of the Artifactory server to promote from if using art:property commands")
    subparser.add_argument("--url", help="Artifactory server url, like: https://<address>/artifactory")
    subparser.add_argument("--user", help="User name for the repository")
    subparser.add_argument("--password", help="Password for the user name (instead of token)")
    subparser.add_argument("--token", help="Token for the repository (instead of password)")
    args = parser.parse_args(*args)

    url, user, password = get_url_user_password(args)
    if not url.endswith("/"):
        url += "/"

    ref_pattern = ListPattern(args.pattern, rrev="*", prev="*")
    lru_aql = get_lru_aql(args.remote, timelimit(args.lru), get_item_path(ref_pattern))
    response = _request(url, user, password, "post", "api/search/aql", lru_aql)

    if args.dry_run:
        ConanOutput().info(response)
        return


def _request(url, user, password, request_type, request_url, plain_data=None):
    try:
        return json.loads(api_request(request_type, f"{url}{request_url}", user, password, plain_data=plain_data))
    except Exception as e:
        raise ConanException(f"Error requesting {request_url}: {e}")


def get_lru_aql(remote, time_limit, path):
    return f"""
    items
    .find({{
        "repo": "{remote}",
        "$and": [{{
            "$or": [
                {{"stat.downloaded": {{"$lt": {time_limit} }} }},
                {{"stat.downloaded": {{"$eq": null}} }}
            ]
        }}],
        "path": {{"$match": "destination/{path}" }},
        "name": "conan_package.tgz"
    }})
    .include("repo", "stat.downloaded", "path")
    """


def get_item_path(ref_pattern):
    name = ref_pattern.name or "*"
    version = ref_pattern.version or "*"
    user = ref_pattern.user or "*"
    channel = ref_pattern.channel or "*"
    rrev = ref_pattern.rrev or "*"
    package_id = ref_pattern.package_id or "*"
    prev = ref_pattern.prev or "*"
    return f"{user}/{name}/{version}/{channel}/{rrev}/package/{package_id}/{prev}/"
