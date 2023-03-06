from conan.tools.files import copy
import os


def deploy(graph, output_folder):
    """Copies all the licenses from all the dependencies of the recipe"""
    for name, dep in graph.root.conanfile.dependencies.items():
        copy(graph.root.conanfile, "(COPY|COPYING|LICENSE).*",
             src=dep.folders.source_folder,
             dst=os.path.join(output_folder, "dependencies_licenses", str(dep)),
             keep_path=False)
