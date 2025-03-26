import os
import shutil
from subprocess import run

from conan.api.conan_api import ConanAPI
from conan.api.output import ConanOutput
from conan.cli.command import conan_command
from conan.cli.args import common_graph_args
from conan.errors import ConanException

from _lipo import lipo as lipo_folder


_valid_archs = [
    'x86',
    'x86_64',
    'armv7',
    'armv8',
    'armv8_32',
    'armv8.3',
    'armv7s',
    'armv7k'
]

@conan_command(group="Consumer")
def deploy_lipo(conan_api: ConanAPI, parser, *args):
    """
    Deploy dependencies for multiple profiles and lipo into universal binaries
    """
    common_graph_args(parser)
    parsed = parser.parse_args(*args)
    profiles = parsed.profile_host or parsed.profile
    if not profiles:
        raise ConanException("Please provide profiles with -pr or -pr:h")
    other_args = []
    i = 0
    while i < len(args[0]):
        arg = args[0][i]
        if arg in ['-pr', '-pr:h', '--profile', '--profile:host']:
            i += 2
        else:
            other_args.append(arg)
            i += 1
    for profile in profiles:
        run(['conan', 'install',
             '--deploy=full_deploy',
             '-pr:h', profile
             ] + other_args)
    output_dir = os.path.join('full_deploy', 'host')
    for package in os.listdir(output_dir):
        package_dir = os.path.join(output_dir, package)
        for version in os.listdir(package_dir):
            version_dir = os.path.join(package_dir, version)
            for build in os.listdir(version_dir):
                d = os.path.join(version_dir, build)
                archs = [os.path.join(d, x) for x in os.listdir(d) if x in _valid_archs]
                # We could skip if len(archs) == 1 but the dir layout would be different
                lipo_folder(d, archs)
                for arch in archs:
                    shutil.rmtree(arch)
