import os
import shutil

from conan.tools.files import copy
from conans.util.files import rmdir
from conan.tools.apple import is_apple_os

from tools_lipo import lipo_tree


def deploy(graph, output_folder, **kwargs):
    # Note the kwargs argument is mandatory to be robust against future changes.
    conanfile = graph.root.conanfile
    conanfile.output.info(f"lipo deployer to {output_folder}")
    for name, dep in graph.root.conanfile.dependencies.items():
        if dep.package_folder is None:
            continue
        folder_name = os.path.join("full_deploy", dep.context, dep.ref.name, str(dep.ref.version))
        build_type = dep.info.settings.get_safe("build_type")
        arch = dep.info.settings.get_safe("arch")
        if build_type:
            folder_name = os.path.join(folder_name, build_type)
        if arch and not is_apple_os(conanfile):
            folder_name = os.path.join(folder_name, arch)
        new_folder = os.path.join(output_folder, folder_name)
        if is_apple_os(conanfile):
            lipo_tree(conanfile, new_folder, [dep.package_folder], add=True)
        else:
            rmdir(new_folder)
            shutil.copytree(dep.package_folder, new_folder, symlinks=True)
        dep.set_deploy_folder(new_folder)
