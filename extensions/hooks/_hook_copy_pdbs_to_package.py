from conan.tools.files import copy
import glob
import json
import os
import re
from io import StringIO
from conan.errors import ConanException
from conans.util.env import get_env


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
        program_files = get_env("ProgramFiles(x86)") or get_env("ProgramFiles")
        conanfile.run(
            rf'"{program_files}\Microsoft Visual Studio\Installer\vswhere.exe" -find "**\dumpbin.exe" -format json',
            stdout=output, scope="")
        match = re.search(r'\[(.*?)\]', str(output.getvalue()), re.DOTALL)
        dumpbin_path = json.loads(f'[{match.group(1)}]')[0]
    except ConanException:
        raise ConanException(
            "Failed to locate dumpbin.exe which is needed to locate the PDBs and copy them to package folder.")

    for dll_path in package_dll:
        # Use dumpbin to get the pdb path from each dll
        dumpbin_output = StringIO()
        pdbpath_flag = "-PDBPATH" if conanfile.win_bash else "/PDBPATH"
        conanfile.run(rf'"{dumpbin_path}" {pdbpath_flag} "{dll_path}"', stdout=dumpbin_output)
        dumpbin = str(dumpbin_output.getvalue())
        pdb_path = re.search(r"[“'\"].*\.pdb[”'\"]", dumpbin)
        if pdb_path:
            pdb_path = pdb_path.group()[1:-1]
            pdb_file = os.path.basename(pdb_path)
            src_path = os.path.dirname(pdb_path)
            dst_path = os.path.dirname(dll_path)
            if src_path != dst_path:  # if pdb is not allready in the package folder, then copy
                # Copy the corresponding pdb file from the build to the package folder
                conanfile.output.info(
                    f"copying {pdb_file} from {src_path} to {dst_path}")
                copy(conanfile, os.path.basename(pdb_path), os.path.dirname(pdb_path), os.path.dirname(dll_path))
            else:
                conanfile.output.info(f"PDB file {pdb_file} already in destination folder {dst_path}, skipping copy")
