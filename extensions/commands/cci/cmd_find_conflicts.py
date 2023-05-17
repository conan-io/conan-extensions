import json

from conan import ConanFile
from conan.api.output import ConanOutput, Color, cli_out_write
from conan.cli.args import add_profiles_args
from conan.cli.command import conan_command, OnceArgument
from typing import Optional

from conan.cli.printers.graph import print_graph_basic


def latest_ref(conan_api, remote, name: str) -> Optional[str]:
    refs = conan_api.search.recipes(name, remote=remote)
    return str(max(refs))


def json_formatter(result):
    cli_out_write(json.dumps(result, indent=4))


@conan_command(group="Conan Center Index", formatters={"json": json_formatter})
def find_conflicts(conan_api, parser, *args):
    """
    Bleeeh
    """
    parser.add_argument('-l', '--list', action=OnceArgument,
                       help="YAML file with list of recipes to export. All the recipes on the list will be exported")
    parser.add_argument("-r", "--remote", default=None, action=OnceArgument,
                        help="Remote names. Accepts wildcards ('*' means all the remotes available)")

    add_profiles_args(parser)
    args = parser.parse_args(*args)

    profile_host, profile_build = conan_api.profiles.get_profiles_from_args(args)
    remote = conan_api.remotes.get(args.remote)

    errors = []

    with open(args.list, 'r') as f:
    #     lines = [line.strip() for line in f]
    #     refs = [latest_ref(conan_api, remote, line) for line in lines]
    #     print(refs)
    #     seen_refs = dict()
    #     for ref in refs:
    #         deps_graph = conan_api.graph.load_graph_requires([ref], [],
    #                                                          profile_host, profile_build, lockfile=None,
    #                                                          remotes=[remote], update=False,
    #                                                          check_updates=False)
    #         if deps_graph.error:
    #             ConanOutput().info("Graph error", Color.BRIGHT_RED)
    #             ConanOutput().info("    {}".format(deps_graph.error), Color.BRIGHT_RED)
    #             errors.append({"ref": ref, "error": str(deps_graph.error)})
    #         for dep in deps_graph.nodes[2:]:
    #             seen_refs.setdefault(str(dep.ref), []).append(ref)
    # refs = [ref.split('/')[0] for ref in seen_refs.keys()]
    # duplicated = list(ref for ref in refs if refs.count(ref) > 1)
        lines = [line.strip() for line in f]
        refs = [latest_ref(conan_api, remote, line) for line in lines]
        print(refs)
        seen_refs = dict()
        deps_graph = conan_api.graph.load_graph_requires(refs, [],
                                                         profile_host, profile_build, lockfile=None,
                                                         remotes=[remote], update=False,
                                                         check_updates=False)
        if deps_graph.error:
            ConanOutput().info("Graph error", Color.BRIGHT_RED)
            ConanOutput().info("    {}".format(deps_graph.error), Color.BRIGHT_RED)
            errors.append(str(deps_graph.error))
    return {
        # "seen_refs": seen_refs,
        # "duplicated": duplicated,
        "errors": errors
    }
