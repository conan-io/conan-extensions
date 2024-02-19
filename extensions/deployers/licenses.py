import os
import zipfile
from conan.api.output import ConanOutput
from conan.tools.files import copy, rmdir

# USE **KWARGS to be robust against changes
def deploy(graph, output_folder, **kwargs):
    out = ConanOutput("deployer(licenses)")
    conanfile = graph.root.conanfile
    files = []
    
    # Cleanup before we start :)
    tmp_dir = os.path.join(output_folder, "licenses")
    if os.path.exists(tmp_dir):
        rmdir(conanfile, tmp_dir)

    # For each dep
    for r, d in conanfile.dependencies.items():
        if d.package_folder is None:
            continue
        
        # Look for a licenses folder
        search_dir = os.path.join(d.package_folder, "licenses") # This is the CCI convention
        if not os.path.isdir(search_dir):
            continue

        # Grab all the files and copy them to a temp dir (this is what we will zip)
        for f in os.listdir(search_dir):
            src = os.path.join(search_dir)
            # Let's kep the name and version so we know which belongs to whats
            dst = os.path.join(tmp_dir, str(d.ref))
            out.debug(src)
            out.debug(dst)
            copy(conanfile, f, src, dst) # Using the conan help because it make's parent folders
            files.append(os.path.join(str(d.ref),f))

    out.trace(files)
    with zipfile.ZipFile(os.path.join(output_folder, 'licenses.zip'), 'w') as licenses_zip:
        for f in files:
            file = os.path.join(tmp_dir, f)
            licenses_zip.write(file, arcname=f, compress_type=zipfile.ZIP_DEFLATED)
            os.remove(file) # Delete all the files we copied! This is so the source control stays clean
