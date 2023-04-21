import os
import json
import textwrap
from multiprocessing.pool import ThreadPool

import yaml

from conan.api.output import ConanOutput, cli_out_write
from conan.cli.command import conan_command, OnceArgument
from conan.cli.printers.graph import print_graph_packages
from conan.cli.args import add_profiles_args
from conan.errors import ConanException
from conan.api.model import ListPattern, PackagesList
from conans.client.graph.graph import RECIPE_CONSUMER, RECIPE_VIRTUAL


def _download_parallel(parallel, conan_api, refs, prefs, remote):

    thread_pool = ThreadPool(parallel)
    # First the recipes in parallel, we have to make sure the recipes are downloaded before the
    # packages
    ConanOutput().info("Downloading recipes in %s parallel threads" % parallel)
    thread_pool.starmap(conan_api.download.recipe, [(ref, remote) for ref in refs])
    thread_pool.close()
    thread_pool.join()

    # Then the packages in parallel
    if prefs:
        thread_pool = ThreadPool(parallel)
        ConanOutput().info("Downloading binary packages in %s parallel threads" % parallel)
        thread_pool.starmap(conan_api.download.package,  [(pref, remote) for pref in prefs])
        thread_pool.close()
        thread_pool.join()


@conan_command(group="Custom Commands")
def promote_dependency_graph(conan_api, parser, *args):
    """
    Copies one dependency graph from one remote to another
    """
    parser.add_argument("path", help="Path to a folder containing a conanfile")

    parser.add_argument("--remote-origin", help="Origin remote to copy from")
    parser.add_argument("--remote-dest", help="Destination remote to copy to")

    parser.add_argument("--name", action=OnceArgument,
                        help='Provide a package name if not specified in conanfile')
    parser.add_argument("--version", action=OnceArgument,
                        help='Provide a package version if not specified in conanfile')
    parser.add_argument("--user", action=OnceArgument,
                        help='Provide a user if not specified in conanfile')
    parser.add_argument("--channel", action=OnceArgument,
                        help='Provide a channel if not specified in conanfile')

    parser.add_argument("-l", "--lockfile", action=OnceArgument,
                        help="Path to a lockfile. Use --lockfile=\"\" to avoid automatic use of "
                             "existing 'conan.lock' file")
    parser.add_argument("--lockfile-partial", action="store_true",
                        help="Do not raise an error if some dependency is not found in lockfile")
    parser.add_argument("--build-require", action='store_true', default=False,
                           help='Whether the provided reference is a build-require')

    parser.add_argument("--only-recipe", action='store_true', default=False,
                        help='Download only the recipe/s, not the binary packages.')
    parser.add_argument('-p', '--package-query', default=None, action=OnceArgument,
                        help="Only download packages matching a specific query. e.g: os=Windows AND "
                             "(arch=x86 OR compiler=gcc)")
    add_profiles_args(parser)
    args = parser.parse_args(*args)

    cwd = os.getcwd()
    path = conan_api.local.get_conanfile_path(args.path, cwd, py=None) if args.path else None

    # Basic collaborators, remotes, lockfile, profiles
    remote_origin = conan_api.remotes.get(args.remote_origin)
    lockfile = conan_api.lockfile.get_lockfile(lockfile=args.lockfile,
                                               conanfile_path=path,
                                               cwd=cwd,
                                               partial=args.lockfile_partial)
    profile_host, profile_build = conan_api.profiles.get_profiles_from_args(args)

    deps_graph = conan_api.graph.load_graph_consumer(path, args.name, args.version,
                                                     args.user, args.channel,
                                                     profile_host, profile_build, lockfile,
                                                     [remote_origin], False,
                                                     check_updates=False,
                                                     is_build_require=args.build_require)
    conan_api.graph.analyze_binaries(deps_graph, [], remotes=[remote_origin], update=False, lockfile=lockfile)
    print_graph_packages(deps_graph)
    global_bundle = PackagesList()

    if deps_graph.root is None:
        ConanOutput().info("Empty graph")
    for dep in deps_graph.root.conanfile.dependencies.values():
        pref_repr_notime = dep.ref.repr_notime()
        ConanOutput().info(f"Adding {pref_repr_notime} to download list")
        ref_pattern = ListPattern(pref_repr_notime, package_id="*", only_recipe=args.only_recipe)
        try:
            select_bundle = conan_api.list.select(ref_pattern, args.package_query, [])
            global_bundle.recipes.update(select_bundle.recipes)
        except Exception as e:
            ConanOutput().warning(f"Skipping {pref_repr_notime}: {e}")
    refs = []
    prefs = []
    for ref, recipe_bundle in global_bundle.refs():
        refs.append(ref)
        for pref, _ in global_bundle.prefs(ref, recipe_bundle):
            prefs.append(pref)
    parallel = conan_api.config.get("core.download:parallel", default=1, check_type=int)
    if parallel <= 1:
        for ref in refs:
            conan_api.download.recipe(ref, remote_origin)
        for pref in prefs:
            conan_api.download.package(pref, remote_origin)
    else:
        _download_parallel(parallel, conan_api, refs, prefs, remote_origin)

    dest_remote = conan_api.remotes.get(args.remote_dest)
    conan_api.upload.check_upstream(global_bundle, dest_remote, False)

    # Remote origin as this operation fetches the exports_sources if needed
    conan_api.upload.prepare(global_bundle, [remote_origin])
    conan_api.upload.upload(global_bundle, dest_remote)


