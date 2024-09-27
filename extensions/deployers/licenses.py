import os
import zipfile
from conan.api.output import ConanOutput


# USE **KWARGS to be robust against changes
def deploy(graph, output_folder, **kwargs):
    out = ConanOutput("deployer(licenses)")
    conanfile = graph.root.conanfile

    # For each dep
    with zipfile.ZipFile(os.path.join(output_folder, 'licenses.zip'), 'w') as licenses_zip:
        for r, d in conanfile.dependencies.items():
            if d.package_folder is None:
                continue

            # Look for a licenses folder
            search_dir = os.path.join(d.package_folder, "licenses")  # This is the CCI convention
            if not os.path.isdir(search_dir):
                continue

            # Grab all the files and write them in the zipfile
            for root, _, files in os.walk(search_dir):
                # Let's keep the name and version so we know which belongs to what
                for file in files:
                    src = os.path.join(root, file)
                    dst = os.path.join(str(d.ref.name), str(d.ref.version), os.path.relpath(root, search_dir), file)
                    out.debug(f"Copying {src} to {dst}")
                    licenses_zip.write(src, arcname=dst, compress_type=zipfile.ZIP_DEFLATED)
