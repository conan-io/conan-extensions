import os
import pathlib
import shutil
import subprocess
from conan.api.conan_api import ConanAPI
from conan.api.output import ConanOutput
from conan.cli.command import conan_command, conan_subcommand
from conan.errors import ConanException


# These are for optimization only, to avoid unnecessarily reading files.
_binary_exts = ['.a', '.dylib']
_regular_exts = [
    '.h', '.hpp', '.hxx', '.c', '.cc', '.cxx', '.cpp', '.m', '.mm', '.txt', '.md', '.html', '.jpg', '.png'
]

def is_macho_binary(file_path):
    """
    Determines if file_path is a Mach-O binary or fat binary
    """
    ext = os.path.splitext(file_path)[1]
    if ext in _binary_exts:
        return True
    if ext in _regular_exts:
        return False
    with open(file_path, "rb") as f:
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
    subparser.add_argument("input_path", help="Root path for the Conan deployment.")
    subparser.add_argument("--output-folder", help="Optional root path for the output."
                           "If not specified, output will be generated in a 'universal' folder inside input_path.",
                           default=None)
    subparser.add_argument("-a", "--architecture", nargs='+', help="Each architecture that will be added to the resulting "
                           "universal binary. If not used, all found architectures will be added.",
                           default=[])
    args = parser.parse_args(*args)

    output = ConanOutput()

    input_path = pathlib.Path(args.input_path)
    output_path = pathlib.Path(args.output_folder or ".")

    if not input_path.exists() or not input_path.is_dir():
        raise ConanException(
            f"The input path '{args.input_path}' is not valid or does not exist.")

    def process_build_type(build_type_path, output_build_type_path, valid_architectures):
        if valid_architectures:
            architectures = [d for d in build_type_path.iterdir() if d.is_dir() and d.name in valid_architectures]
        else:
            architectures = [d for d in build_type_path.iterdir() if d.is_dir()]

        all_archs = valid_architectures or [d.name for d in architectures]

        output.info(f"Creating universal binaries for architectures: {', '.join(all_archs)}")

        if len(architectures) < 2:
            raise ConanException(f"Less than two architectures found in folder {build_type_path}")

        combined_arch_name = ".".join(sorted([d.name for d in architectures]))

        # Identify all files in the first architecture to check if they are Mach-O binaries
        first_arch_files = list(architectures[0].glob("**/*"))  # Recursively find all files
        for file in first_arch_files:
            if file.is_file():
                relative_path = file.relative_to(build_type_path)
                relative_path_without_arch = pathlib.Path(*list(relative_path.parts)[1:])
                output_relative_path = combined_arch_name / pathlib.Path(*list(relative_path.parts)[1:])
                ouput_path = output_build_type_path / output_relative_path
                if is_macho_binary(str(file)):
                    # This file is a Mach-O binary, attempt to create a lipo binary with files from other architectures
                    arch_files = [str(architecture / relative_path_without_arch) for architecture in architectures]
                    ouput_path.parent.mkdir(parents=True, exist_ok=True)
                    lipo_args = ["lipo", "-create"] + arch_files + ["-output", str(ouput_path)]
                    output.info(f"Creating universal binary {ouput_path} for: {', '.join(arch_files)}")
                    subprocess.run(lipo_args)
                else:
                    # Not a Mach-O binary, simply copy the file to the destination tree
                    ouput_path.parent.mkdir(parents=True, exist_ok=True)
                    output.info(f"Copying: {file} -> {ouput_path}")
                    shutil.copy(file, ouput_path)

    # Traverse the input_path
    for lib_name in input_path.iterdir():
        if lib_name.is_dir():
            for version in lib_name.iterdir():
                if version.is_dir():
                    for build_type in version.iterdir():
                        if build_type.is_dir():
                            output_build_type_path = output_path / lib_name.name / version.name / build_type.name
                            process_build_type(build_type, output_build_type_path, args.architecture)


@conan_subcommand()
def lipo_info(conan_api: ConanAPI, parser, subparser, *args):
    """
    Get information for lipo files
    """
    # TODO: implement

    args = parser.parse_args(*args)
