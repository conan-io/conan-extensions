import os

from conan.cli.command import conan_command, conan_subcommand
from conans.util.files import save, mkdir


@conan_command(group='Consumer')
def develop(conan_api, parser, *args):
    """
    Manage the Conan configuration in the Conan home.
    """


@conan_subcommand()
def develop_new(conan_api, parser, subparser, *args):
    """
    Generate a new empty folder with a .conanrc pointing a folder there
    """
    subparser.add_argument("path", help="Path to the folder where the .conanrc will be created")

    args = parser.parse_args(*args)
    base_path = os.path.realpath(args.path)
    conan_rc_path = os.path.join(base_path, ".conanrc")
    config_home = os.path.join(base_path, ".conan_home")
    mkdir(base_path)
    mkdir(config_home)
    save(conan_rc_path, "conan_home=./.conan_home")
