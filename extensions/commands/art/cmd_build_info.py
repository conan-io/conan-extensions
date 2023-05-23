import base64
import datetime
import json
import os
import re
import hashlib
from pathlib import Path

import requests

from conan.api.conan_api import ConanAPI
from conan.api.output import cli_out_write
from conan.cli.command import conan_command, conan_subcommand
from conan.errors import ConanException
from conans.model.recipe_ref import RecipeReference
from conan import conan_version

from cmd_server import read_servers

SERVERS_FILENAME = ".art-servers"


def response_to_str(response):
    content = response.content
    try:
        # A bytes message, decode it as str
        if isinstance(content, bytes):
            content = content.decode('utf-8')

        content_type = response.headers.get("content-type")

        if content_type == "application/json":
            # Errors from Artifactory looks like:
            #  {"errors" : [ {"status" : 400, "message" : "Bla bla bla"}]}
            try:
                data = json.loads(content)["errors"][0]
                content = "{}: {}".format(data["status"], data["message"])
            except Exception:
                pass
        elif "text/html" in content_type:
            content = "{}: {}".format(response.status_code, response.reason)

        return content

    except Exception:
        return response.content


def api_request(method, request_url, user=None, password=None, json_data=None,
                sign_key_name=None):
    headers = {}
    if json_data:
        headers.update({"Content-Type": "application/json"})
    if sign_key_name:
        headers.update({"X-JFrog-Crypto-Key-Name": sign_key_name})

    requests_method = getattr(requests, method)
    if user and password:
        response = requests_method(request_url, auth=(
            user, password), data=json_data, headers=headers)
    else:
        response = requests_method(request_url)

    if response.status_code == 401:
        raise Exception(response_to_str(response))
    elif response.status_code not in [200, 204]:
        raise Exception(response_to_str(response))

    return response_to_str(response)


def get_remote_path(rrev, package_id=None, prev=None):
    ref = RecipeReference.loads(rrev)
    user = ref.user or "_"
    channel = ref.channel or "_"
    rev_path = f"{user}/{ref.name}/{ref.version}/{channel}/{ref.revision}"
    if not package_id:
        return f"{rev_path}/export"
    else:
        assert prev
        return f"{rev_path}/package/{package_id}/{prev}"


def get_hashes(file_path):
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


def get_node_by_id(nodes, id):
    for node in nodes:
        if node.get("id") == int(id):
            return node

def get_formatted_time():
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


def transitive_requires(nodes, node_id, include_root=False, invert_order=False):
    requires_mapping = {node['id']: node['requires'] for node in nodes}

    def dfs_paths(node, visited, path, result):
        visited.add(node)
        path.append(node)
        if not requires_mapping[node]:
            result.append(path.copy())
        else:
            for required_id_str in requires_mapping[node].keys():
                required_id = int(required_id_str)
                if required_id not in visited:
                    dfs_paths(required_id, visited, path, result)
        visited.remove(node)
        path.pop()

        return result

    visited = set()
    paths = list(dfs_paths(node_id, visited, [], []))
    paths = paths if include_root else [path[1:] for path in paths]
    paths = [path[::-1] for path in paths] if invert_order else paths
    return paths


def sublists_from_id(list_of_lists, target_id):
    result = []
    for sublist in list_of_lists:
        if target_id in sublist:
            index = sublist.index(target_id)
            new_sublist = sublist[(index + 1):]
            result.append(new_sublist)
    return result


def get_requested_by(nodes, node_id, artifact_type):
    sublists = sublists_from_id(transitive_requires(nodes, 0, invert_order=True), node_id)
    ret = []
    for nodes_ids in sublists:
        ref_list = []
        for node_id in nodes_ids:
            node = get_node_by_id(nodes, node_id)
            pkg = f":{node.get('package_id')}#{node.get('prev')}" if artifact_type == "package" else ""
            ref_list.append(f"{node.get('ref')}{pkg}")
        ret.append(ref_list)
    return ret


def unique_requires(transitive_reqs):
    unique_deps = set()
    for dependencies in transitive_reqs:
        unique_deps.update(dependencies)
    return sorted(list(unique_deps))


class BuildInfo:

    def __init__(self, graph, name, number, repository, with_dependencies=False, 
                 url=None, user=None, password=None):
        self._graph = graph
        self._name = name
        self._number = number
        self._repository = repository
        self._url = url
        self._user = user
        self._password = password
        self._cached_artifact_info = {}
        self._with_dependencies = with_dependencies

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
            remote_path = get_remote_path(node.get('ref'))
        else:
            artifacts_names = ["conan_package.tgz", "conaninfo.txt", "conanmanifest.txt"]
            remote_path = get_remote_path(node.get('ref'), node.get("package_id"), node.get("prev"))

        def _get_local_artifacts():
            local_artifacts = []
            artifacts_folder = node.get("package_folder") if artifact_type == "package" else node.get("recipe_folder")
            dl_folder = Path(artifacts_folder).parents[0] / "d"
            file_list = list(dl_folder.glob("*"))
            if len(file_list) >= 3:
                for file_path in dl_folder.glob("*"):
                    if file_path.is_file():
                        file_name = file_path.name
                        md5, sha1, sha256 = get_hashes(file_path)
                        artifact_info = {"type": os.path.splitext(file_name)[1].lstrip('.'),
                                         "sha256": sha256,
                                         "sha1": sha1,
                                         "md5": md5}

                        if not is_dependency:
                            artifact_info.update({"name": file_name, "path": f'{self._repository}/{remote_path}/{file_name}'})
                        else:
                            ref = node.get("ref")
                            pkg = f":{node.get('package_id')}#{node.get('prev')}" if artifact_type == "package" else ""
                            artifact_info.update({"id": f"{ref}{pkg} :: {file_name}"})

                        local_artifacts.append(artifact_info)
            return local_artifacts

        def _get_remote_artifacts():
            assert self._url and self._repository, "Missing information in the Conan local cache, " \
                                                   "please provide the --url and --repository arguments " \
                                                   "to retrieve the information from Artifactory."

            remote_artifacts = []

            for artifact in artifacts_names:
                request_url = f"{self._url}/api/storage/{self._repository}/{remote_path}/{artifact}"
                if not self._cached_artifact_info.get(request_url):
                    checksums = None
                    try:
                        response = api_request("get", request_url, self._user, self._password)
                        response_data = json.loads(response)
                        checksums = response_data.get("checksums")
                        self._cached_artifact_info[request_url] = checksums
                    except Exception:
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

                    remote_artifacts.append(artifact_info)

            return remote_artifacts

        artifacts = _get_local_artifacts()

        if not artifacts:
            # we don't have the artifacts in the local cache
            # it's possible that the packages came from an install without a build
            # so let's ask Artifactory about the checksums of the packages
            # we can use the Conan API to get the enabled remotes and iterate through them
            # but it may be better to use a specific repo when creating the build info ?
            artifacts = _get_remote_artifacts()

        if not artifacts:
            raise ConanException(f"There are no artifacts for the {node.get('ref')} {artifact_type}. "
                                 "Probably the package was not uploaded before creating the Build Info."
                                 "Please upload the package to the server and try again.")

        # complete the information for the artifacts:
        if is_dependency:
            requested_by = get_requested_by(self._graph["graph"]["nodes"], node.get("id"), artifact_type)
            for artifact in artifacts:
                artifact.update({"requestedBy": requested_by})

        return artifacts

    def get_modules(self):
        ret = []
        try:
            nodes = self._graph["graph"]["nodes"]
        except KeyError:
            raise ConanException("JSON does not contain graph information")

        for node in nodes:
            ref = node.get("ref")
            if ref and ref != "conanfile":
                transitive_reqs = transitive_requires(nodes, node.get("id"))
                unique_reqs = unique_requires(transitive_reqs)

                # only add the nodes that were marked as built
                if node.get("binary") == "Build":

                    # recipe module
                    module = {
                        "type": "conan",
                        "id": str(ref),
                        "artifacts": self.get_artifacts(node, "recipe")
                    }

                    if self._with_dependencies:
                        all_dependencies = []
                        for require_id in unique_reqs:
                            deps_artifacts = self.get_artifacts(get_node_by_id(nodes, require_id), "recipe",
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
                            for require_id in unique_reqs:
                                deps_artifacts = self.get_artifacts(get_node_by_id(nodes, require_id), "package",
                                                                    is_dependency=True)
                                all_dependencies.extend(deps_artifacts)

                            module.update({"dependencies": all_dependencies})

                        ret.append(module)

        return ret

    def header(self):
        return {"version": "1.0.1",
                "name": self._name,
                "number": self._number,
                "agent": {},
                "started": get_formatted_time(),
                "buildAgent": {"name": "conan", "version": f"{str(conan_version)}"}}

    def create(self):
        bi = self.header()
        bi.update({"modules": self.get_modules()})
        return json.dumps(bi, indent=4)


def manifest_from_build_info(build_info, repository, with_dependencies=True):
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
                full_path = repository + "/" + get_remote_path(rrev, pkgid, prev) + "/" + filename
                if not any(d['path'] == full_path for d in manifest["files"]):
                    manifest["files"].append({"path": full_path, "checksum": dependency.get("sha256")})
    return manifest


# def read_servers():
#     # FIXME: this code is repeated at art:server command, feature to reuse code importing from other modules is needed
#     path = os.path.join(os.path.dirname(__file__), SERVERS_FILENAME)
#     servers = []
#     if os.path.exists(path):
#         with open(path) as servers_file:
#             data_encoded = servers_file.read()
#             data = base64.b64decode(data_encoded).decode('utf-8')
#             servers_data = json.loads(data)
#             servers = servers_data["servers"]
#     return servers


def get_server(server_name):
    servers = read_servers()
    server_names = [s["name"] for s in servers]
    if server_name not in server_names:
        raise ConanException(f"The server specified ({server_name}) is not configured. "
                             f"Use `conan art:server add {server_name}` to configure it.")
    for server in servers:
        if server["name"] == server_name:
            return server


def assert_server_or_url_user_password(args):
    if args.server and args.url:
        raise ConanException("--server and --url (with --user & --password) flags cannot be used together.")
    if not args.server and not args.url:
        raise ConanException("Specify --server or --url (with --user & --password) flags to contact Artifactory.")
    if args.url:
        if not args.user or not args.password:
            raise ConanException("Specify --user and --password to use with the --url flag to contact Artifactory.")
    assert args.server or (args.url and args.user and args.password)


def get_url_user_password(args):
    if args.server:
        server_name = args.server.strip()
        server = get_server(server_name)
        url = server.get("url")
        user = server.get("user")
        password = server.get("password")
    else:
        url = args.url
        user = args.user
        password = args.password
    return url, user, password


@conan_command(group="Custom commands")
def build_info(conan_api: ConanAPI, parser, *args):
    """
    Manages JFROG BuildInfo
    """


@conan_subcommand()
def build_info_create(conan_api: ConanAPI, parser, subparser, *args):
    """
    Creates BuildInfo from a Conan graph json from a conan install or create.
    """

    subparser.add_argument("json", help="Conan generated JSON output file.")
    subparser.add_argument("build_name", help="Build name property for BuildInfo.")
    subparser.add_argument("build_number", help="Build number property for BuildInfo.")
    subparser.add_argument("repository", help="Repository to look artifacts for.")

    subparser.add_argument("--server", help="Server name of the Artifactory to get the build info from")
    subparser.add_argument("--url", help="Artifactory url, like: https://<address>/artifactory. "
                                         "This may be not necessary if all the information for the Conan "
                                         "artifacts is present in the local cache.")
    subparser.add_argument("--user", help="user name for the repository")
    subparser.add_argument("--password", help="password for the user name")

    subparser.add_argument("--with-dependencies", help="Whether to add dependencies information or not. Default: false.",
                           action='store_true', default=False)

    args = parser.parse_args(*args)

    url, user, password = get_url_user_password(args)

    with open(args.json, 'r') as f:
        data = json.load(f)

    bi = BuildInfo(data, args.build_name, args.build_number, args.repository, 
                   with_dependencies=args.with_dependencies, url=url, user=user, password=password)

    cli_out_write(bi.create())


@conan_subcommand()
def build_info_upload(conan_api: ConanAPI, parser, subparser, *args):
    """
    Uploads BuildInfo json to repository.
    """

    subparser.add_argument("build_info", help="BuildInfo json file.")

    subparser.add_argument("--server", help="Server name of the Artifactory to get the build info from")
    subparser.add_argument("--url", help="Artifactory url, like: https://<address>/artifactory")
    subparser.add_argument("--user", help="user name for the repository")
    subparser.add_argument("--password", help="password for the user name")

    args = parser.parse_args(*args)
    assert_server_or_url_user_password(args)

    url, user, password = get_url_user_password(args)

    with open(args.build_info) as f:
        build_info_json = json.load(f)

    # FIXME: this code is repeated in the art:property command,
    # we have to fix that custom commands can share modules between them

    # first, set the properties build.name and build.number 
    # for the artifacts in the BuildInfo

    build_name = build_info_json.get("name")
    build_number = build_info_json.get("number")

    for module in build_info_json.get('modules'):
        for artifact in module.get('artifacts'):
            artifact_properties = {}
            artifact_path = artifact.get('path')
            try:
                request_url = f"{url}/api/storage/{artifact_path}?properties"
                props_response = api_request("get", request_url, user, password)
                artifact_properties = json.loads(props_response).get("properties")
            except:
                pass

            artifact_properties.setdefault("build.name", []).append(build_name)
            artifact_properties.setdefault("build.number", []).append(build_number)        

            request_url = f"{url}/api/metadata/{artifact_path}"
            api_request("patch", request_url, user, password, json_data=json.dumps({"props": artifact_properties}))


    # now upload the BuildInfo
    request_url = f"{url}/api/build"
    response = api_request("put", request_url, user, password, json_data=json.dumps(build_info_json))
    cli_out_write(response)


@conan_subcommand()
def build_info_promote(conan_api: ConanAPI, parser, subparser, *args):
    """
    Promote the BuildInfo from the source to the target repository.
    """

    subparser.add_argument("build_name", help="BuildInfo name to promote.")
    subparser.add_argument("build_number", help="BuildInfo number to promote.")
    subparser.add_argument("source_repo", help="Source repo for promotion.")
    subparser.add_argument("target_repo", help="Target repo for promotion.")

    subparser.add_argument("--dependencies", help="Whether to copy the build's dependencies or not. Default: false.",
                           action='store_true', default=False)
    subparser.add_argument("--comment", help="An optional comment describing the reason for promotion. Default: ''")

    subparser.add_argument("--server", help="Server name of the Artifactory to get the build info from")
    subparser.add_argument("--url", help="Artifactory url, like: https://<address>/artifactory")
    subparser.add_argument("--user", help="user name for the repository")
    subparser.add_argument("--password", help="password for the user name")

    args = parser.parse_args(*args)
    assert_server_or_url_user_password(args)

    url, user, password = get_url_user_password(args)

    promotion_json = {
        "sourceRepo": args.source_repo,
        "targetRepo": args.target_repo,
        # Conan promotions must always be copy, and the clean must be handled manually
        # otherwise you can end up deleting recipe artifacts that other packages use
        "copy": "true",
        "dependencies": "true" if args.dependencies else "false",
        "comment": args.comment
    }

    request_url = f"{url}/api/build/promote/{args.build_name}/{args.build_number}"

    response = api_request("post", request_url, user, password, json_data=json.dumps(promotion_json))

    cli_out_write(response)


@conan_subcommand()
def build_info_get(conan_api: ConanAPI, parser, subparser, *args):
    """
    Get Build Info information.
    """

    subparser.add_argument("build_name", help="BuildInfo name to get.")
    subparser.add_argument("build_number", help="BuildInfo number to get.")

    subparser.add_argument("--server", help="Server name of the Artifactory to get the build info from")
    subparser.add_argument("--url", help="Artifactory url, like: https://<address>/artifactory")
    subparser.add_argument("--user", help="user name for Artifactory")
    subparser.add_argument("--password", help="password for the user name for Artifactory")

    args = parser.parse_args(*args)

    assert_server_or_url_user_password(args)
    url, user, password = get_url_user_password(args)

    request_url = f"{url}/api/build/{args.build_name}/{args.build_number}"
    response = api_request("get", request_url, user, password)

    cli_out_write(response)


@conan_subcommand()
def build_info_delete(conan_api: ConanAPI, parser, subparser, *args):
    """
    Removes builds stored in Artifactory. Useful for cleaning up old build info data.
    """

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

    subparser.add_argument("--server", help="Server name of the Artifactory to get the build info from")
    subparser.add_argument("--url", help="Artifactory url, like: https://<address>/artifactory")
    subparser.add_argument("--user", help="user name for the repository")
    subparser.add_argument("--password", help="password for the user name")

    args = parser.parse_args(*args)
    assert_server_or_url_user_password(args)

    url, user, password = get_url_user_password(args)

    delete_json = {
        "buildName": args.build_name,
        "buildNumbers": args.build_number,
        "deleteArtifacts": "true" if args.delete_artifacts else "false",
        "deleteAll": "true" if args.delete_all else "false",
    }

    request_url = f"{url}/api/build/delete"

    response = api_request("post", request_url, user, password, json_data=json.dumps(delete_json))

    cli_out_write(response)


@conan_subcommand()
def build_info_append(conan_api: ConanAPI, parser, subparser, *args):
    """
    Append published build to the build info.
    """

    subparser.add_argument("build_name", help="The current build name.")
    subparser.add_argument("build_number", help="The current build number.")

    subparser.add_argument("--server", help="Server name of the Artifactory to get the build info from")
    subparser.add_argument("--url", help="Artifactory url, like: https://<address>/artifactory")
    subparser.add_argument("--user", help="user name for the repository")
    subparser.add_argument("--password", help="password for the user name")

    subparser.add_argument("--build-info", help="Name and number for the Build Info already published in Artifactory. You can add multiple Builds " \
                                                "like --build-info=build_name,build_number --build-info=build_name,build_number",
                           action="append")

    args = parser.parse_args(*args)
    assert_server_or_url_user_password(args)

    url, user, password = get_url_user_password(args)

    for build_info in args.build_info:
        if not "," in build_info:
            raise ConanException("Please, provide the build name and number to append in the format: --build-info=build_name,build_number")

    all_modules = []

    for build_info in args.build_info:
        name, number = build_info.split(",")
        request_url = f"{url}/api/build/{name}/{number}"
        response = api_request("get", request_url, user, password)
        json_data = json.loads(response)
        build_info = json_data.get("buildInfo")
        for module in build_info.get("modules"):
            # avoid repeating shared recipe modules between builds
            if not any(d['id'] == module.get('id') for d in all_modules):
                all_modules.append(module)

    bi = BuildInfo(None, args.build_name, args.build_number, None)
    bi_json = bi.header()
    bi_json.update({"modules": all_modules})
    cli_out_write(json.dumps(bi_json, indent=4))


@conan_subcommand()
def build_info_create_bundle(conan_api: ConanAPI, parser, subparser, *args):
    """
    Creates an Artifactory Release Bundle from the information of the Build Info
    """

    subparser.add_argument("json", help="BuildInfo JSON.")

    subparser.add_argument("repository", help="Repository where artifacts are located.")

    subparser.add_argument("bundle_name", help="The created bundle name.")
    subparser.add_argument("bundle_version", help="The created bundle version.")

    subparser.add_argument("sign_key_name", help="Signing Key name.")

    subparser.add_argument("--server", help="Server name of the Artifactory to get the build info from")
    subparser.add_argument("--url", help="Artifactory url, like: https://<address>/artifactory")
    subparser.add_argument("--user", help="user name for the repository")
    subparser.add_argument("--password", help="password for the user name")

    args = parser.parse_args(*args)
    assert_server_or_url_user_password(args)

    url, user, password = get_url_user_password(args)

    with open(args.json, 'r') as f:
        data = json.load(f)

    manifest = manifest_from_build_info(data, args.repository, with_dependencies=True)

    bundle_json = {
        "payload": manifest
    }

    request_url = f"{url}/api/release_bundles/from_files/{args.bundle_name}/{args.bundle_version}"

    response = api_request("post", request_url, user, password, json_data=json.dumps(bundle_json),
                           sign_key_name=args.sign_key_name)

    cli_out_write(response)
