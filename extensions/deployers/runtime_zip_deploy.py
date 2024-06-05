import os
import shutil
import zipfile


# USE **KWARGS to be robust against changes
def deploy(graph, output_folder, **kwargs):
    conanfile = graph.root.conanfile
    files = []
    for r, d in conanfile.dependencies.items():
        if d.package_folder is None:
            continue
        # look for .dlls and .exes in the bin folder
        search_dirs = (d.cpp_info.bindirs or []) + (d.cpp_info.libdirs or [])
        for dir in search_dirs:
            search_dir = os.path.join(d.package_folder, dir)
            if not os.path.isdir(search_dir):
                continue
            for f in os.listdir(search_dir):
                src = os.path.join(search_dir, f)
                if f.endswith(".dll") or f.endswith(".exe") or f.endswith(".dylib") or os.access(src, os.X_OK):
                    dst = os.path.join(output_folder, f)
                    shutil.copy2(src, dst)
                    files.append(dst)

    with zipfile.ZipFile(os.path.join(output_folder, 'runtime.zip'), 'w') as myzip:
        for f in files:
            myzip.write(f, os.path.basename(f), compress_type=zipfile.ZIP_DEFLATED)
            os.remove(f)
