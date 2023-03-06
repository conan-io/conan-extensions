from conan.tools.files import copy
import os


def deploy(graph, output_folder):
    """Copies the sources of every dependency of the recipe into its output folder"""
    for name, dep in graph.root.conanfile.dependencies.items():
        copy(graph.root.conanfile, "*", dep.folders.source_folder, os.path.join(output_folder, "dependencies_sources", str(dep)))
