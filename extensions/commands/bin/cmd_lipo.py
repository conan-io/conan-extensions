import os
import pathlib
from conan.api.conan_api import ConanAPI
from conan.cli.command import conan_command, conan_subcommand
from conan.errors import ConanException


@conan_command(group="Binary manipulation")
def lipo(conan_api: ConanAPI, parser, *args):
    """
    Wrapper over lipo to manage universal binaries for Apple OS's.
    """


@conan_subcommand()
def lipo_create(conan_api: ConanAPI, parser, subparser, *args):
    """
    Create lipo binaries from the results of a Conan full_deploy. It expects a folder structure as: 
    <input_path>/<name>/<version>/<build_type>/<architecture>
    """
    subparser.add_argument("input_path", help="Root path for the Conan deployment. Needs ")
    subparser.add_argument("-a", "--architecture", help="Each architecture that will be added to the resulting "
                           "universal binary. If not used, all found architectures will be added.", 
                           action="append")
    subparser.add_argument("--name-filter", help="", 
                           action="append")
    subparser.add_argument("--build-type-filter", help="", 
                           action="append")
    args = parser.parse_args(*args)

    input_path = pathlib(args.input_path)

    if not input_path.exists() or not input_path.is_dir():
        raise ConanException(f"The input path is not valid.")


@conan_subcommand()
def lipo_info(conan_api: ConanAPI, parser, subparser, *args):
    """
    Get information for lipo files
    """

    args = parser.parse_args(*args)
