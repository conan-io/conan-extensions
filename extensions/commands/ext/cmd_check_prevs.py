from conan.api.conan_api import ConanAPI
from conan.api.model import MultiPackagesList, ListPattern, PackagesList, PkgReference
from conan.api.output import ConanOutput

from conan.cli import make_abs_path
from conan.cli.command import conan_command, OnceArgument
from conan.cli.commands.list import print_list_text, print_list_json, print_list_compact
from conan.cli.formatters.list import list_packages_html

from conan.errors import ConanException


@conan_command(group="Extension", formatters={"text": print_list_text,
                                              "json": print_list_json,
                                              "html": list_packages_html,
                                              "compact": print_list_compact})
def check_prevs(conan_api: ConanAPI, parser, *args):
    """
    Ensure that the selected references only contains 1 package revision in the given remotes
    """
    parser.add_argument('pattern', nargs="?",
                        help="A pattern in the form 'pkg/version#revision:package_id#revision', "
                             "e.g: \"zlib/1.2.13:*\" means all binaries for zlib/1.2.13. "
                             "If revision is not specified, it is assumed latest one.")
    parser.add_argument("-l", "--list", help="Package list file")
    parser.add_argument('-p', '--package-query', default=None, action=OnceArgument,
                        help="Only upload packages matching a specific query. e.g: os=Windows AND "
                             "(arch=x86 OR compiler=gcc)")
    parser.add_argument("-r", "--remote", action="append", default=None,
                        help='Look in the specified remote or remotes server')

    args = parser.parse_args(*args)
    remotes = conan_api.remotes.list(args.remote)

    if args.pattern is None and args.list is None:
        raise ConanException("Missing pattern or package list file")
    if args.pattern and args.list:
        raise ConanException("Cannot define both the pattern and the package list file")
    if args.package_query and args.list:
        raise ConanException("Cannot define package-query and the package list file")

    result = MultiPackagesList()

    for remote in remotes:
        if args.list:
            listfile = make_abs_path(args.list)
            multi_package_list = MultiPackagesList.load(listfile)
            if remote.name not in multi_package_list.lists:
                ConanOutput().warning(f"No packages for remote '{remote.name}' were found "
                                      "in the package list, skipping it.")
                continue
            pkglist = multi_package_list[remote.name]
        else:
            ref_pattern = ListPattern(args.pattern, rrev=None, prev="*")
            if not ref_pattern.package_id:
                raise ConanException("The pattern must include a package_id, e.g: "
                                     "\"zlib/1.2.13:*\" means all binaries for zlib/1.2.13")
            pkglist = conan_api.list.select(ref_pattern, args.package_query, remote)
        remote_pkglist = PackagesList()
        # Can't iterate packages because we might have been not given a package revision
        for ref, _ in pkglist.items():
            recipe_dict = pkglist.recipe_dict(ref)
            for package_id, pkg_info in recipe_dict.get("packages", {}).items():
                prevs = pkg_info.get("revisions", {})
                revisions = []
                if len(prevs) > 1:
                    # No need to ask the server (again if coming from the select endpoint)
                    # we already know there are multiple revisions for this package_id
                    for prev in prevs:
                        revisions.append(PkgReference(ref, package_id, prev))
                else:
                    revisions = conan_api.list.package_revisions(PkgReference(ref, package_id),
                                                                 remote)
                if len(revisions) > 1:
                    remote_pkglist.add_ref(ref)
                    for pref in revisions:
                        remote_pkglist.add_pref(pref)
                    result.add(remote.name, remote_pkglist)

    return {
        "conan_error": "Multiple package revisions found" if result.lists else None,
        "results": result.serialize(),
    }
