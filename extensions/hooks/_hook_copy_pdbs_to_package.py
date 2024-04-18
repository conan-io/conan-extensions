from conan.tools.files import copy
import glob
import json
import os
import re
from io import StringIO
from conans.errors import ConanException


def post_package(conanfile):
    if conanfile.settings.get_safe("os") != "Windows" or conanfile.settings.get_safe("compiler") != "msvc":
        return
    conanfile.output.info("PDBs post package hook running")
    search_package_dll = os.path.join(conanfile.package_folder, "**/*.dll")
    package_dll = glob.glob(search_package_dll, recursive=True)
    if len(package_dll) == 0:
        return
    # Find dumpbin path
    output = StringIO()
    try:
        conanfile.run(
            r'"%ProgramFiles(x86)%\Microsoft Visual Studio\Installer\vswhere.exe" -find "**\dumpbin.exe" -format json',
            stdout=output)
    except ConanException:
        raise ConanException(
            "Failed to locate dumpbin.exe which is needed to locate the PDBs and copy them to package folder.")
    dumpbin_path = json.loads(str(output.getvalue()))[0]

    for dll_path in package_dll:
        # Use dumpbin to get the pdb path from each dll
        dumpbin_output = StringIO()
        conanfile.run(rf'"{dumpbin_path}" /PDBPATH {dll_path}', stdout=dumpbin_output)
        dumpbin = str(dumpbin_output.getvalue())
        pdb_path = re.search(r"'.*\.pdb'", dumpbin)
        if pdb_path:
            pdb_path = pdb_path.group()[1:-1]
        # Copy the corresponding pdb file from the build to the package folder
        conanfile.output.info(
            f"copying {os.path.basename(pdb_path)} from {os.path.dirname(pdb_path)} to {os.path.dirname(dll_path)}")
        copy(conanfile, os.path.basename(pdb_path), os.path.dirname(pdb_path), os.path.dirname(dll_path))
