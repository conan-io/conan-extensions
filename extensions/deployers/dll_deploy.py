import os, shutil

def deploy(graph, output_folder, **kwargs):
    conanfile = graph.root.conanfile
    conanfile.output.info(f"Deploying the dll...")
    for req, dep in conanfile.dependencies.items():
        conanfile.output.verbose(f"Searching for dll in {dep.ref}...")
        if dep.package_folder is None:
            conanfile.output.verbose(f"{dep.ref} does not have any package folder")
            continue
        if not dep.cpp_info.bindirs:
            conanfile.output.verbose(f"{dep.ref} does not have any bin directory")
            continue
        for bindir_name in dep.cpp_info.bindirs:
            bindir_path = os.path.join(dep.package_folder, bindir_name)
            if not os.path.isdir(bindir_path):
                conanfile.output.verbose(f"{bindir_path} does not exist")
                continue
            file_count = 0
            for file_name in os.listdir(bindir_path):
                if file_name.endswith(".dll"):
                    file_count += 1
                    file_path = os.path.join(bindir_path, file_name)
                    dst = os.path.join(output_folder, "bin", file_name)
                    conanfile.output.verbose(f"Copy {file_path} in {dst}")
                    shutil.copy2(file_path, dst)
            conanfile.output.info(f"Copied {file_count} dll from {dep.ref}")
    conanfile.output.info(f"Deployed all dll!")
