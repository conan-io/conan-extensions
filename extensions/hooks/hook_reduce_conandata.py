import os
import yaml

from conan.tools.files import load, save


def load_yml(conanfile, path):
    if os.path.isfile(path):
        return yaml.safe_load(load(conanfile, path))
    return None


def post_export(conanfile):
    if conanfile.conf.get('user.hooks:reduce_conandata', check_type=bool, default=False):
        conandata_path = os.path.join(conanfile.export_folder, "conandata.yml")
        version = str(conanfile.version)

        conandata_yml = load_yml(conanfile, conandata_path)
        if not conandata_yml:
            return
        info = {}
        for entry in conandata_yml:
            if version not in conandata_yml[entry]:
                continue
            info[entry] = {}
            info[entry][version] = conandata_yml[entry][version]
        conanfile.output.info("Saving conandata.yml: {}".format(info))
        new_conandata_yml = yaml.safe_dump(info, default_flow_style=False)
        conanfile.output.info("New conandata.yml contents: {}".format(new_conandata_yml))
        save(conanfile, conandata_path, new_conandata_yml)
