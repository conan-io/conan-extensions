from conan.tools.files import copy
import glob
import json
import os
import re


def post_package(conanfile):
    # Find dumpbin path
    conanfile.run(
        r'"%ProgramFiles(x86)%\Microsoft Visual Studio\Installer\vswhere.exe" -find "**\dumpbin.exe" -format json > out.json')
    with open("out.json") as f:
        dumpbin_path = json.load(f)[0]

    # Find all dll paths in the package folder
    search_package_dll = os.path.join(conanfile.package_folder, "**/*.dll")
    package_dll = glob.glob(search_package_dll, recursive=True)
    for dll_path in package_dll:
        # Use dumpbin to get the pdb path from each dll
        conanfile.run(rf'"{dumpbin_path}" /PDBPATH {dll_path} > out.txt')
        with open("out.txt") as f:
            dumpbin = f.read()
        pdb_path = re.search(r"'.*\.pdb'", dumpbin)
        if pdb_path:
            pdb_path = pdb_path.group().replace("'", "")

        # Copy the corresponding pdb file from the build to the package folder
        conanfile.output.info(
            f"copying {os.path.basename(pdb_path)} from {os.path.dirname(pdb_path)} to {os.path.dirname(dll_path)}")
        copy(conanfile, os.path.basename(pdb_path), os.path.dirname(pdb_path), os.path.dirname(dll_path))
