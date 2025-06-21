import copy
import json
import os
import shutil
from subprocess import run
import sys
import tempfile
from contextlib import redirect_stdout

from conan.api.conan_api import ConanAPI
from conan.api.output import ConanOutput
from conan.cli import make_abs_path
from conan.cli.args import common_graph_args, validate_common_graph_args
from conan.cli.command import conan_command
from conan.cli.formatters.graph import format_graph_json
from conan.cli.printers import print_profiles
from conan.cli.printers.graph import print_graph_packages, print_graph_basic
from conan.errors import ConanException


@conan_command(group="Consumer", formatters={"json": format_graph_json})
def install_universal(conan_api: ConanAPI, parser, *args):
    """
    Install universal packages from the requirements specified in a recipe (conanfile.py or conanfile.txt).

    It can also be used to install packages without a conanfile, using the
    --requires and --tool-requires arguments.

    If any requirement is not found in the local cache, it will iterate the remotes
    looking for it. When the full dependency graph is computed, and all dependencies
    recipes have been found, it will look for binary packages matching the current settings.
    If no binary package is found for some or several dependencies, it will error,
    unless the '--build' argument is used to build it from source.

    After installation of packages, the generators and deployers will be called.
    """
    common_graph_args(parser)
    parser.add_argument("-g", "--generator", action="append", help='Generators to use')
    parser.add_argument("-of", "--output-folder",
                        help='The root output folder for generated and build files')
    parser.add_argument("-d", "--deployer", action="append",
                        help="Deploy using the provided deployer to the output folder. "
                             "Built-in deployers: 'full_deploy', 'direct_deploy', 'runtime_deploy'")
    parser.add_argument("--deployer-folder",
                        help="Deployer output folder, base build folder by default if not set")
    parser.add_argument("--deployer-package", action="append",
                        help="Execute the deploy() method of the packages matching "
                             "the provided patterns")
    parser.add_argument("--build-require", action='store_true', default=False,
                        help='Whether the provided path is a build-require')
    parser.add_argument("--envs-generation", default=None, choices=["false"],
                        help="Generation strategy for virtual environment files for the root")
    args = parser.parse_args(*args)
    validate_common_graph_args(args)
    # basic paths
    cwd = os.getcwd()
    path = conan_api.local.get_conanfile_path(args.path, cwd, py=None) if args.path else None
    source_folder = os.path.dirname(path) if args.path else cwd
    output_folder = make_abs_path(args.output_folder, cwd) if args.output_folder else None

    # Basic collaborators: remotes, lockfile, profiles
    remotes = conan_api.remotes.list(args.remote) if not args.no_remote else []
    overrides = eval(args.lockfile_overrides) if args.lockfile_overrides else None
    lockfile = conan_api.lockfile.get_lockfile(lockfile=args.lockfile, conanfile_path=path, cwd=cwd,
                                               partial=args.lockfile_partial, overrides=overrides)
    profile_host, profile_build = conan_api.profiles.get_profiles_from_args(args)
    print_profiles(profile_host, profile_build)

    args_build = args.build

    # Handle universal packages
    do_universal = profile_host.settings["os"] in ["Macos", "iOS", "watchOS", "tvOS", "visionOS"] and "|" in profile_host.settings["arch"]
    arch_data = {}
    if do_universal:
        universal = build_universal(conan_api, profile_host, profile_build, path, remotes=remotes, overrides=overrides, lockfile=lockfile, args=args)
        arch_data = universal["arch_data"]
        args_build = universal["refs"]
        if not args_build:
            args_build = ["never"]

    # Graph computation (without installation of binaries)
    gapi = conan_api.graph
    if path:
        deps_graph = gapi.load_graph_consumer(path, args.name, args.version, args.user, args.channel,
                                              profile_host, profile_build, lockfile, remotes,
                                              args.update, is_build_require=args.build_require)
    else:
        deps_graph = gapi.load_graph_requires(args.requires, args.tool_requires, profile_host,
                                              profile_build, lockfile, remotes, args.update)

    if do_universal:
        for node in deps_graph.ordered_iterate():
            make_universal_conanfile(node.conanfile, args, arch_data)

    print_graph_basic(deps_graph)
    deps_graph.report_graph_error()
    gapi.analyze_binaries(deps_graph, args_build, remotes, update=args.update, lockfile=lockfile)
    print_graph_packages(deps_graph)

    # Installation of binaries and consumer generators
    conan_api.install.install_binaries(deps_graph=deps_graph, remotes=remotes)
    ConanOutput().title("Finalizing install (deploy, generators)")
    conan_api.install.install_consumer(deps_graph, args.generator, source_folder, output_folder,
                                       deploy=args.deployer, deploy_package=args.deployer_package,
                                       deploy_folder=args.deployer_folder,
                                       envs_generation=args.envs_generation)
    ConanOutput().success("Install finished successfully")

    # Update lockfile if necessary
    lockfile = conan_api.lockfile.update_lockfile(lockfile, deps_graph, args.lockfile_packages,
                                                  clean=args.lockfile_clean)
    conan_api.lockfile.save_lockfile(lockfile, args.lockfile_out, cwd)
    return {"graph": deps_graph,
            "conan_api": conan_api}


def build_universal(conan_api: ConanAPI, profile_host, profile_build, path, remotes, overrides, lockfile, args):
    # Compute universal package build order
    gapi = conan_api.graph
    if path:
        deps_graph = gapi.load_graph_consumer(path, args.name, args.version, args.user, args.channel,
                                              profile_host, profile_build, lockfile, remotes,
                                              args.update, is_build_require=args.build_require)
    else:
        deps_graph = gapi.load_graph_requires(args.requires, args.tool_requires, profile_host,
                                              profile_build, lockfile, remotes, args.update)
    deps_graph.report_graph_error()
    gapi.analyze_binaries(deps_graph, args.build, remotes, update=args.update, lockfile=lockfile)

    install_graph = conan_api.graph.build_order(deps_graph, "recipe", True,
                                                profile_args=args)
    install_order_serialized = install_graph.install_build_order()
    arch_data = {}
    refs = [node["ref"] for nodes in install_order_serialized["order"] for node in nodes]
    if refs:
        archs = str(profile_host.settings["arch"]).split("|")
        for arch in archs:
            ConanOutput().title(f"Preparing {arch} binaries")

            arch_args = copy.deepcopy(args)
            arch_args.settings_host = (arch_args.settings_host or []) + [f"arch={arch}"]
            arch_profile_host, arch_profile_build = conan_api.profiles.get_profiles_from_args(arch_args)
            print_profiles(arch_profile_host, arch_profile_build)

            # Graph computation (without installation of binaries)
            arch_deps_graph = gapi.load_graph_requires(refs, [], arch_profile_host,
                                                        arch_profile_build, lockfile, remotes, args.update)

            print_graph_basic(arch_deps_graph)
            arch_deps_graph.report_graph_error()
            gapi.analyze_binaries(arch_deps_graph, ["missing"], remotes, update=args.update, lockfile=lockfile)
            print_graph_packages(arch_deps_graph)

            # Installation of binaries and consumer generators
            conan_api.install.install_binaries(deps_graph=arch_deps_graph, remotes=remotes)

            with tempfile.TemporaryFile(mode="w+") as f:
                with redirect_stdout(f):
                    format_graph_json({
                        "graph": arch_deps_graph,
                        "conan_api": conan_api})
                f.seek(0)
                arch_data[arch] = json.load(f)["graph"]["nodes"].values()

    return {
        "arch_data": arch_data,
        "refs": refs}


def make_universal_conanfile(conanfile, args, arch_data):
    def _generate(conanfile):
        pass
    def _build(conanfile):
        pass
    def _find_arch_package(conanfile, arch):
        nodes = [n for n in arch_data[arch] if n["name"] == conanfile.name and n["version"] == conanfile.version]
        if not nodes:
            raise ConanException(f"Unable to find {conanfile.name} package for {arch}")
        return nodes[0]
    def _package(conanfile):
        archs = str(conanfile.settings.arch).split("|")
        lipo_tree(conanfile.package_folder, [_find_arch_package(conanfile, arch)["package_folder"] for arch in archs])
    if conanfile.settings.get_safe("arch", "") and conanfile.package_type not in ("header-library", "build-scripts", "python-require"):
        setattr(conanfile, "generate", _generate.__get__(conanfile, type(conanfile)))
        setattr(conanfile, "build", _build.__get__(conanfile, type(conanfile)))
        setattr(conanfile, "package", _package.__get__(conanfile, type(conanfile)))


# Lipo support

# These are for optimization only, to avoid unnecessarily reading files.
_binary_exts = ['.a', '.dylib']
_regular_exts = [
    '.h', '.hpp', '.hxx', '.c', '.cc', '.cxx', '.cpp', '.m', '.mm', '.txt', '.md', '.html', '.jpg', '.png', '.class'
]


def is_macho_binary(filename):
    ext = os.path.splitext(filename)[1]
    if ext in _binary_exts:
        return True
    if ext in _regular_exts:
        return False
    with open(filename, "rb") as f:
        header = f.read(4)
        if header == b'\xcf\xfa\xed\xfe':
            # cffaedfe is Mach-O binary
            return True
        elif header == b'\xca\xfe\xba\xbe':
            # cafebabe is Mach-O fat binary
            return True
        elif header == b'!<arch>\n':
            # ar archive
            return True
    return False


def is_macho_fat_binary(filename):
    ext = os.path.splitext(filename)[1]
    if ext in _binary_exts:
        return True
    if ext in _regular_exts:
        return False
    with open(filename, "rb") as f:
        header = f.read(4)
        if header == b'\xcf\xfa\xed\xfe':
            # cffaedfe is Mach-O binary
            return False
        elif header == b'\xca\xfe\xba\xbe':
            # cafebabe is Mach-O fat binary
            return True
        elif header == b'!<arch>\n':
            # ar archive
            return False
    return False


def copy_arch_file(src, dst, top=None, arch_folders=()):
    if os.path.isfile(src):
        if top and arch_folders and is_macho_binary(src):
            # Try to lipo all available archs on the first path.
            src_components = src.split(os.path.sep)
            top_components = top.split(os.path.sep)
            if src_components[:len(top_components)] == top_components:
                paths = [os.path.join(a, *(src_components[len(top_components):])) for a in arch_folders]
                paths = [p for p in paths if os.path.isfile(p)]
                if len(paths) > 1:
                    try:
                        run(['lipo', '-output', dst, '-create'] + paths, check=True)
                    except Exception:
                        if not is_macho_fat_binary(src):
                            raise
                        # otherwise we have two fat binaries with multiple archs
                        # so just copy one.
                    else:
                        return
        if os.path.exists(dst):
            pass # don't overwrite existing files
        else:
            shutil.copy2(src, dst)


# Modified copytree to copy new files to an existing tree.
def graft_tree(src, dst, symlinks=False, copy_function=shutil.copy2, dirs_exist_ok=False):
    names = os.listdir(src)
    os.makedirs(dst, exist_ok=dirs_exist_ok)
    errors = []
    for name in names:
        srcname = os.path.join(src, name)
        dstname = os.path.join(dst, name)
        try:
            if symlinks and os.path.islink(srcname):
                if os.path.exists(dstname):
                    continue
                linkto = os.readlink(srcname)
                os.symlink(linkto, dstname)
            elif os.path.isdir(srcname):
                graft_tree(srcname, dstname, symlinks, copy_function, dirs_exist_ok)
            else:
                copy_function(srcname, dstname)
            # What about devices, sockets etc.?
        # catch the Error from the recursive graft_tree so that we can
        # continue with other files
        except shutil.Error as err:
            errors.extend(err.args[0])
        except OSError as why:
            errors.append((srcname, dstname, str(why)))
    try:
        shutil.copystat(src, dst)
    except OSError as why:
        # can't copy file access times on Windows
        if why.winerror is None: # pylint: disable=no-member
            errors.extend((src, dst, str(why)))
    if errors:
        raise shutil.Error(errors)

def lipo_tree(dst_folder, arch_folders):
    for folder in arch_folders:
        graft_tree(folder,
                   dst_folder,
                   symlinks=True,
                   copy_function=lambda s, d, top=folder: copy_arch_file(s, d,
                                                                         top=top,
                                                                         arch_folders=arch_folders),
                   dirs_exist_ok=True)
