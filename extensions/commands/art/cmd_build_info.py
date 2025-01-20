import datetime
import json
import os
import re
import hashlib
from pathlib import Path

from conan.api.conan_api import ConanAPI
from conan.api.output import cli_out_write, ConanOutput
from conan.cli.command import conan_command, conan_subcommand
from conan.errors import ConanException
try:
    from conan.internal.model.recipe_ref import RecipeReference
except:
    from conans.model.recipe_ref import RecipeReference
from conan import conan_version
from conan.tools.scm import Version

from utils import NotFoundException, api_request, assert_server_or_url_user_password, load_json
from cmd_property import get_properties, set_properties
from cmd_server import get_url_user_password


def get_buildinfo(build_name, build_number, url, user, password, project=None):
    request_url = f"{url}/api/build/{build_name}/{build_number}"
    if project is not None:
        request_url = f"{request_url}?project={project}"
    build_info = api_request("get", request_url, user, password)
    return build_info


def _get_remote_path(rrev, package_id=None, prev=None):
    ref = RecipeReference.loads(rrev)
    user = ref.user or "_"
    channel = ref.channel or "_"
    rev_path = f"{user}/{ref.name}/{ref.version}/{channel}/{ref.revision}"
    if not package_id:
        return f"{rev_path}/export"
    else:
        assert prev
        return f"{rev_path}/package/{package_id}/{prev}"


def _get_hashes(file_path):
    buf_size = 65536

    md5 = hashlib.md5()
    sha1 = hashlib.sha1()
    sha256 = hashlib.sha256()

    with open(file_path, 'rb') as f:
        while True:
            data = f.read(buf_size)
            if not data:
                break
            md5.update(data)
            sha1.update(data)
            sha256.update(data)
    return md5.hexdigest(), sha1.hexdigest(), sha256.hexdigest()


def _get_formatted_time():
    now = datetime.datetime.now(datetime.timezone.utc)
    local_tz_offset = now.astimezone().strftime('%z')
    formatted_time = now.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + local_tz_offset

    # Apparently if the timestamp has the Z the BuildInfo is not correctly identified in Artifactory
    # if local_tz_offset == "+0000":
    #    formatted_time = formatted_time[:-5] + "Z"

    # from here: https://github.com/jfrog/build-info-go/blob/9b6f2ec13eedc41ad0f66882e630c2882f90cc76/buildinfo-schema.json#L63
    if not re.match(r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}.\d{3}(Z|[+-]\d{4})$', formatted_time):
        raise ValueError("Time format does not match BuildInfo required format.")

    return formatted_time


def _get_requested_by(nodes, node_id, artifact_type):

    node_id = str(node_id)
    root_direct = []
    root_node_id = "1"
    requested_by_ids = []

    for id, node in nodes["1"].get("dependencies").items():
        if node.get("direct") == "True":
            root_direct.append(id)

    if node_id in root_direct:
        requested_by_ids.append([root_node_id])
    else:
        for direct_id in root_direct:
            direct_node = nodes.get(direct_id)
            all_requested_by = []
            if node_id in direct_node.get("dependencies"):
                sublist = list(nodes.get(direct_id).get("dependencies").keys())
                sublist.reverse()
                all_requested_by = sublist + [direct_id, root_node_id]
            if all_requested_by:
                requested_by_ids.append(all_requested_by)

    ret = []
    for nodes_ids in requested_by_ids:
        ref_list = []
        for node_id in nodes_ids:
            node = nodes.get(node_id)
            pkg = f":{node.get('package_id')}#{node.get('prev')}" if artifact_type == "package" else ""
            ref_list.append(f"{node.get('ref')}{pkg}")
        ret.append(ref_list)
    return ret


class _BuildInfo:

    def __init__(self, graph, name, number, repository, build_url=None, with_dependencies=False, 
                 add_cached_deps=False, url=None, user=None, password=None):
        self._graph = graph
        self._name = name
        self._number = number
        self._repository = repository
        self._url = url
        self._user = user
        self._build_url = build_url
        self._password = password
        self._cached_artifact_info = {}
        self._with_dependencies = with_dependencies
        self._add_cached_deps = add_cached_deps

    def get_artifacts(self, node, artifact_type, is_dependency=False):
        """
        Function to get artifact information, those artifacts can be added as artifacts of a
        module or as artifacts from dependencies and depending on that the format is
        different. For artifacts of modules they have the keys 'name' and 'path'. If they come
        from a dependency they have an 'id' instead of 'name' and they don't have 'path'.
        """

        assert artifact_type in ["recipe", "package"]

        if artifact_type == "recipe":
            artifacts_names = ["conan_sources.tgz", "conan_export.tgz", "conanfile.py", "conanmanifest.txt"]
        else:
            artifacts_names = ["conan_package.tgz", "conaninfo.txt", "conanmanifest.txt"]

        def _get_local_artifacts():
            local_artifacts = []
            missing_artifacts = []
            artifacts_folder = node.get("package_folder") if artifact_type == "package" else node.get("recipe_folder")
            if artifacts_folder is None and artifact_type == "package" and node.get("binary") == "Skip":
                ConanOutput().warning(f"Package is marked as 'Skip' for {node.get('ref')} and will not be included "
                                      "into the Build Info. If you want to get it included, use "
                                      "conf -c a:tools.graph:skip_binaries=False in your conan create/install command.")
                return (local_artifacts, missing_artifacts)

            artifacts_folder = Path(node.get("package_folder")) if artifact_type == "package" else Path(node.get("recipe_folder"))
            dl_folder = artifacts_folder.parents[0] / "d"
            dl_folder_files = [file for file in dl_folder.glob("*") if file.name in artifacts_names]
            artifacts_folder_files = [file for file in artifacts_folder.glob("*") if file.name in artifacts_names]
            all_files = dl_folder_files + artifacts_folder_files
            
            processed_files = set()
            
            for file_path in all_files:
                file_name = file_path.name
                if file_path.is_file() and file_name not in processed_files:
                    processed_files.add(file_path.name)
                    md5, sha1, sha256 = _get_hashes(file_path)
                    artifact_info = {"type": os.path.splitext(file_name)[1].lstrip('.'),
                                     "sha256": sha256,
                                     "sha1": sha1,
                                     "md5": md5}

                    if not is_dependency:
                        remote_path = _get_remote_path(
                            node.get('ref')) if artifact_type == "recipe" else _get_remote_path(node.get('ref'),
                                                                                                node.get("package_id"),
                                                                                                node.get("prev"))
                        artifact_info.update({"name": file_name, "path": f'{self._repository}/{remote_path}/{file_name}'})
                    else:
                        ref = node.get("ref")
                        pkg = f":{node.get('package_id')}#{node.get('prev')}" if artifact_type == "package" else ""
                        artifact_info.update({"id": f"{ref}{pkg} :: {file_name}"})

                    local_artifacts.append(artifact_info)

            missing_files = set(artifacts_names) - processed_files
            return (local_artifacts, missing_files)

        def _get_remote_artifacts(artifact):
            artifact_info = None
            assert self._url, "Missing information in the Conan local cache, " \
                              "please provide '--url' or '--server' arguments " \
                              "to retrieve the information from Artifactory."

            remote_path = _get_remote_path(node.get('ref')) if artifact_type == "recipe" else _get_remote_path(
                node.get('ref'), node.get("package_id"), node.get("prev"))

            request_url = f"{self._url}/api/storage/{self._repository}/{remote_path}/{artifact}"

            if not self._cached_artifact_info.get(request_url):
                checksums = None
                try:
                    response = api_request("get", request_url, self._user, self._password)
                    response_data = json.loads(response)
                    checksums = response_data.get("checksums")
                    self._cached_artifact_info[request_url] = checksums
                # pass if not found, maybe we do not have the sources in the repo
                except NotFoundException:
                    pass
            else:
                checksums = self._cached_artifact_info.get(request_url)

            if checksums:
                artifact_info = {"type": os.path.splitext(artifact)[1].lstrip('.'),
                                 "sha256": checksums.get("sha256"),
                                 "sha1": checksums.get("sha1"),
                                 "md5": checksums.get("md5")}

                artifact_path = f'{self._repository}/{remote_path}/{artifact}'
                if not is_dependency:
                    artifact_info.update({"name": artifact, "path": artifact_path})
                else:
                    ref = node.get("ref")
                    pkg = f":{node.get('package_id')}#{node.get('prev')}" if artifact_type == "package" else ""
                    artifact_info.update({"id": f"{ref}{pkg} :: {artifact}"})

            return artifact_info

        artifacts, missing = _get_local_artifacts()

        if 'conan_sources.tgz' in missing:
            # check if we have the conan_sources in Artifactory, if it's not there
            # maybe the package comes from an installation that did not build the package
            # so we don't fail if we can't find conan_sources.tgz
            sources_artifact = _get_remote_artifacts("conan_sources.tgz")
            if sources_artifact:
                artifacts.append(sources_artifact)

        folder = node.get("package_folder") if artifact_type == "package" else node.get("recipe_folder")
        if not artifacts and folder:
            raise ConanException(f"There are missing artifacts for the {node.get('ref')} {artifact_type}. "
                                  "Check that you have all the packages installed in the Conan cache when creating the Build Info.")

        # complete the information for the artifacts:

        if is_dependency:
            requested_by = _get_requested_by(self._graph["graph"]["nodes"], node.get("id"), artifact_type)
            for artifact in artifacts:
                artifact.update({"requestedBy": requested_by})

        return artifacts

    def get_modules(self):
        ret = []
        try:
            nodes = self._graph["graph"]["nodes"]
        except KeyError:
            raise ConanException("JSON does not contain graph information")

        for node in nodes.values():
            ref = node.get("ref")
            if ref:
                transitive_dependencies = node.get("dependencies").keys() if node.get("dependencies").keys() else []
                binary = node.get("binary")

                if ref and ((binary == "Build") or (binary in ["Cache", "Download", "Update"] and self._add_cached_deps)):

                    # recipe module
                    module = {
                        "type": "conan",
                        "id": str(ref),
                        "artifacts": self.get_artifacts(node, "recipe")
                    }

                    if self._with_dependencies:
                        all_dependencies = []
                        for require_id in transitive_dependencies:
                            deps_artifacts = self.get_artifacts(nodes.get(require_id), "recipe",
                                                                is_dependency=True)
                            all_dependencies.extend(deps_artifacts)

                        module.update({"dependencies": all_dependencies})

                    ret.append(module)

                    # package module
                    if node.get("package_id") and node.get("prev"):
                        module = {
                            "type": "conan",
                            "id": f'{str(ref)}:{node.get("package_id")}#{node.get("prev")}',
                            "artifacts": self.get_artifacts(node, "package")
                        }
                        # get the dependencies and its artifacts
                        if self._with_dependencies:
                            all_dependencies = []
                            for require_id in transitive_dependencies:
                                deps_artifacts = self.get_artifacts(nodes.get(require_id), "package",
                                                                    is_dependency=True)
                                all_dependencies.extend(deps_artifacts)

                            module.update({"dependencies": all_dependencies})

                        ret.append(module)

        return ret

    def header(self):
        header = {
            "version": "1.0.1",
            "name": self._name,
            "number": self._number,
            "agent": {},
            "started": _get_formatted_time(),
            "buildAgent": {"name": "conan", "version": f"{str(conan_version)}"}
        }

        if self._build_url is not None:
            build_url_json = {
                "url": self._build_url,
            }
            header = {**build_url_json, **header}

        return header

    def create(self):
        bi = self.header()
        bi.update({"modules": self.get_modules()})
        return json.dumps(bi, indent=4)


def _manifest_from_build_info(build_info, repository, with_dependencies=True):
    manifest = {"files": []}
    for module in build_info.get("modules"):
        for artifact in module.get("artifacts"):
            manifest["files"].append({"path": artifact.get("path"), "checksum": artifact.get("sha256")})
        if with_dependencies:
            for dependency in module.get("dependencies"):
                full_reference = dependency.get("id").split("::")[0].strip()
                filename = dependency.get("id").split("::")[1].strip()
                rrev = full_reference.split(":")[0]
                pkgid = None
                prev = None
                if ":" in full_reference:
                    pkgid = full_reference.split(":")[1].split("#")[0]
                    prev = full_reference.split(":")[1].split("#")[1]
                full_path = repository + "/" + _get_remote_path(rrev, pkgid, prev) + "/" + filename
                if not any(d['path'] == full_path for d in manifest["files"]):
                    manifest["files"].append({"path": full_path, "checksum": dependency.get("sha256")})
    return manifest


def _check_min_required_conan_version(min_ver):
    if conan_version < Version(min_ver):
        raise ConanException("This custom command is only compatible with " \
                             f"Conan versions>={min_ver}. Please update Conan.")


def _add_default_arguments(subparser, is_bi_create=False, is_bi_create_bundle=False):
    url_help = "Artifactory url, like: https://<address>/artifactory."
    if is_bi_create:
        url_help += " This may be not necessary if all the information for the Conan artifacts is present in the " \
                    "local cache."
    if not (is_bi_create or is_bi_create_bundle):
        subparser.add_argument("--project", help="Project key for the Build Info in Artifactory", default=None)

    subparser.add_argument("--server", help="Server name of the Artifactory to get the build info from.")
    subparser.add_argument("--url", help=url_help)
    subparser.add_argument("--user", help="User name for the Artifactory server.")
    subparser.add_argument("--password", help="Password for the Artifactory server.")
    subparser.add_argument("--token", help="Token for the Artifactory server.")
    return subparser


@conan_command(group="Artifactory")
def build_info(conan_api: ConanAPI, parser, *args):
    """
    Manages JFrog Build Info (https://www.buildinfo.org/)
    """


@conan_subcommand()
def build_info_create(conan_api: ConanAPI, parser, subparser, *args):
    """
    Creates BuildInfo from a Conan graph json from a conan install or create.
    """
    _add_default_arguments(subparser, is_bi_create=True)

    _check_min_required_conan_version("2.0.6")

    subparser.add_argument("json", help="Conan generated JSON output file.")
    subparser.add_argument("build_name", help="Build name property for BuildInfo.")
    subparser.add_argument("build_number", help="Build number property for BuildInfo.")
    subparser.add_argument("--build-url", help="Build url property for BuildInfo.", default=None, action="store")
    subparser.add_argument("repository", help="Artifactory repository name where artifacts are located -not the conan remote name-.")

    subparser.add_argument("--with-dependencies", help="Whether to add dependencies information or not. Default: false.",
                           action='store_true', default=False)

    subparser.add_argument("--add-cached-deps", help="It will add not only the Conan packages that are built "
                           "but also the ones that are used from the cache but not built. Default: false.",
                           action='store_true', default=False)

    args = parser.parse_args(*args)

    url, user, password = get_url_user_password(args)

    data = load_json(args.json)

    # remove the 'conanfile' node
    data["graph"]["nodes"].pop("0")
    bi = _BuildInfo(data, args.build_name, args.build_number, args.repository,
                    build_url=args.build_url,
                    with_dependencies=args.with_dependencies,
                    add_cached_deps=args.add_cached_deps, url=url, user=user, password=password)

    cli_out_write(bi.create())


@conan_subcommand()
def build_info_upload(conan_api: ConanAPI, parser, subparser, *args):
    """
    Uploads BuildInfo json to repository.
    """
    _add_default_arguments(subparser)

    subparser.add_argument("build_info", help="BuildInfo json file.")

    args = parser.parse_args(*args)
    assert_server_or_url_user_password(args)

    url, user, password = get_url_user_password(args)

    build_info_json = load_json(args.build_info)

    # first, set the properties build.name and build.number
    # for the artifacts in the BuildInfo

    build_name = build_info_json.get("name")
    build_number = build_info_json.get("number")

    for module in build_info_json.get('modules'):
        for artifact in module.get('artifacts'):
            artifact_path = artifact.get('path')
            artifact_properties = get_properties(artifact_path, url, user, password)

            artifact_properties.setdefault("build.name", []).append(build_name)
            artifact_properties.setdefault("build.number", []).append(build_number)        

            set_properties(artifact_properties, artifact_path, url, user, password, False)

    # now upload the BuildInfo
    request_url = f"{url}/api/build"
    if args.project is not None:
        request_url = f"{request_url}?project={args.project}"
    response = api_request("put", request_url, user, password, json_data=json.dumps(build_info_json))
    if response:
        cli_out_write(response)
    else:
        cli_out_write("Build info uploaded successfully.")


@conan_subcommand()
def build_info_promote(conan_api: ConanAPI, parser, subparser, *args):
    """
    Promote the BuildInfo from the source to the target repository.
    """
    _add_default_arguments(subparser)

    subparser.add_argument("build_name", help="BuildInfo name to promote.")
    subparser.add_argument("build_number", help="BuildInfo number to promote.")
    subparser.add_argument("source_repo", help="Artifactory repository to get artifacts from.")
    subparser.add_argument("target_repo", help="Artifactory repository to promote artifacts to.")

    subparser.add_argument("--dependencies", help="Whether to copy the build's dependencies or not. Default: false.",
                           action='store_true', default=False)
    subparser.add_argument("--comment", help="An optional comment describing the reason for promotion. Default: ''")

    args = parser.parse_args(*args)
    assert_server_or_url_user_password(args)

    url, user, password = get_url_user_password(args)

    promotion_json = {
        "sourceRepo": args.source_repo,
        "targetRepo": args.target_repo,
        # Conan's promotions must always be copy, and the clean must be handled manually
        # otherwise you can end up deleting recipe artifacts that other packages use
        "copy": "true",
        "dependencies": "true" if args.dependencies else "false",
        "comment": args.comment
    }

    request_url = f"{url}/api/build/promote/{args.build_name}/{args.build_number}"
    if args.project is not None:
        request_url = f"{request_url}?project={args.project}"
    response = api_request("post", request_url, user, password, json_data=json.dumps(promotion_json))

    if response:
        cli_out_write(response)



@conan_subcommand()
def build_info_get(conan_api: ConanAPI, parser, subparser, *args):
    """
    Get Build Info information.
    """
    _add_default_arguments(subparser)

    subparser.add_argument("build_name", help="BuildInfo name to get.")
    subparser.add_argument("build_number", help="BuildInfo number to get.")

    args = parser.parse_args(*args)

    assert_server_or_url_user_password(args)
    url, user, password = get_url_user_password(args)

    bi_json = get_buildinfo(args.build_name, args.build_number, url, user, password, args.project)

    cli_out_write(bi_json)


@conan_subcommand()
def build_info_delete(conan_api: ConanAPI, parser, subparser, *args):
    """
    Removes builds stored in Artifactory. Useful for cleaning up old build info data.
    """
    _add_default_arguments(subparser)

    subparser.add_argument("build_name", help="BuildInfo name to delete.")

    subparser.add_argument("--build-number", help="BuildInfo numbers to promote. You can add " \
                                                  "several build-numbers for the same build-name, like: --build-number=1 --build-number=2.",
                           action='append')
    subparser.add_argument("--delete-artifacts", help="Build artifacts are also removed " \
                                                      "provided they have the corresponding build.name and build.number properties attached to them. " \
                                                      "Default false.",
                           action='store_true', default=False, )
    subparser.add_argument("--delete-all", help="The whole build is removed. Default false.",
                           action='store_true', default=False, )

    args = parser.parse_args(*args)
    assert_server_or_url_user_password(args)

    url, user, password = get_url_user_password(args)

    delete_json = {
        "buildName": args.build_name,
        "buildNumbers": args.build_number,
        "deleteArtifacts": "true" if args.delete_artifacts else "false",
        "deleteAll": "true" if args.delete_all else "false",
    }
    # Deleting BIs from projets is not documented in the artifactory api: https://jfrog.com/help/r/jfrog-rest-apis/delete-builds
    # the usual url parameter ?project={args.project} does not work here
    if args.project:
        delete_json["project"] = args.project

    request_url = f"{url}/api/build/delete"
    response = api_request("post", request_url, user, password, json_data=json.dumps(delete_json))

    if response:
        cli_out_write(response)


@conan_subcommand()
def build_info_append(conan_api: ConanAPI, parser, subparser, *args):
    """
    Append published build to the build info.
    """
    _add_default_arguments(subparser)

    subparser.add_argument("build_name", help="The current build name.")
    subparser.add_argument("build_number", help="The current build number.")

    subparser.add_argument("--build-info", help="Name and number for the Build Info already published in Artifactory. "
                                                "You can add multiple Builds like --build-info=build_name,build_number"
                                                " --build-info=build_name,build_number",
                           action="append")

    args = parser.parse_args(*args)
    assert_server_or_url_user_password(args)

    url, user, password = get_url_user_password(args)

    for build_info in args.build_info:
        if not "," in build_info:
            raise ConanException("Please, provide the build name and number to append in the format: "
                                 "--build-info=build_name,build_number")

    all_modules = []

    for build_info in args.build_info:
        name, number = build_info.split(",")
        bi_json = get_buildinfo(name, number, url, user, password, args.project)
        bi_data = json.loads(bi_json)
        build_info = bi_data.get("buildInfo")
        for module in build_info.get("modules"):
            # avoid repeating shared recipe modules between builds
            if not any(d['id'] == module.get('id') for d in all_modules):
                all_modules.append(module)

    bi = _BuildInfo(None, args.build_name, args.build_number, None)
    bi_json = bi.header()
    bi_json.update({"modules": all_modules})
    cli_out_write(json.dumps(bi_json, indent=4))


@conan_subcommand()
def build_info_create_bundle(conan_api: ConanAPI, parser, subparser, *args):
    """
    Creates an Artifactory Release Bundle from the information of the Build Info
    """
    _add_default_arguments(subparser, is_bi_create_bundle=True)

    subparser.add_argument("json", help="BuildInfo JSON.")

    subparser.add_argument("repository", help="Artifactory repository where artifacts are located.")

    subparser.add_argument("bundle_name", help="The created bundle name.")
    subparser.add_argument("bundle_version", help="The created bundle version.")

    subparser.add_argument("sign_key_name", help="Signing Key name.")

    args = parser.parse_args(*args)
    assert_server_or_url_user_password(args)

    url, user, password = get_url_user_password(args)

    data = load_json(args.json)

    manifest = _manifest_from_build_info(data, args.repository, with_dependencies=True)

    bundle_json = {
        "payload": manifest
    }

    request_url = f"{url}/api/release_bundles/from_files/{args.bundle_name}/{args.bundle_version}"

    response = api_request("post", request_url, user, password, json_data=json.dumps(bundle_json),
                           sign_key_name=args.sign_key_name)

    if response:
        cli_out_write(response)
