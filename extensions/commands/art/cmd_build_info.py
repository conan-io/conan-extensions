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


def api_request(method, request_url, user=None, password=None, apikey=None, json_data=None):
    headers = {}
    if json_data:
        headers.update({"Content-Type": "application/json"})
    if apikey:
        headers.update({"X-JFrog-Art-Api": apikey})

    requests_method = getattr(requests, method)
    if user and password:
        response = requests_method(request_url, auth=(
            user, password), data=json_data, headers=headers)
    elif apikey:
        response = requests_method(
            request_url, data=json_data, headers=headers)
    else:
        response = requests_method(request_url)

    if response.status_code == 401:
        raise Exception(response_to_str(response))
    elif response.status_code not in [200, 204]:
        raise Exception(response_to_str(response))

    return response_to_str(response)


def get_remote_path(rrev, package_id=None, prev=None):
    ref = RecipeReference.loads(rrev)
    rev_path = f"_/{ref.name}/{ref.version}/_/{ref.revision}"
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


def get_node_by_ref(nodes, ref):
    for node in nodes:
        if node.get("ref") == ref:
            return node


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


def transitive_requires(nodes, node_id, include_root=False):
    requires_mapping = {node['id']: node['requires'] for node in nodes}

    def dfs_paths(node, visited, path):
        visited.add(node)
        path.append(node)
        if not requires_mapping[node]:
            yield path.copy()
        else:
            for required_id_str in requires_mapping[node].keys():
                required_id = int(required_id_str)
                if required_id not in visited:
                    yield from dfs_paths(required_id, visited, path)
        visited.remove(node)
        path.pop()

    visited = set()
    paths = list(dfs_paths(node_id, visited, []))
    dependencies = paths if include_root else [path[1:] for path in paths]

    return dependencies


def unique_requires(transitive_reqs):
    unique_deps = set()
    for dependencies in transitive_reqs:
        unique_deps.update(dependencies)
    return sorted(list(unique_deps))


class BuildInfo:

    def __init__(self, graph, name, number, repositories=None, url=None, user=None, password=None, apikey=None):
        self._graph = graph
        self._name = name
        self._number = number
        self._repositories = repositories
        self._url = url
        self._user = user
        self._password = password
        self._apikey = apikey
        self._cached_artifact_info = {}

    def get_artifacts(self, node, artifact_type, is_dependency=False):
        """
        Function to get artifact information, those artifacts can be added as artifacts of a
        module or as artifacts from dependencies and depending on that the format is
        different. For artifacts of modules they have the keys 'name' and 'path'. If they come
        from a dependency they have an 'id' instead of 'name' and they don't have 'path'.
        """

        assert artifact_type in ["recipe", "package"]

        if artifact_type == "recipe":
            artifacts_names = ["conan_sources.tgz", "conanfile.py", "conanmanifest.txt"]
            remote_path = get_remote_path(node.get('ref'))
        else:
            artifacts_names = ["conan_package.tgz", "conaninfo.txt", "conanmanifest.txt"]
            remote_path = get_remote_path(node.get('ref'), node.get("package_id"), node.get("prev"))

        artifacts = []
        artifacts_folder = node.get("package_folder") if artifact_type == "package" else node.get("recipe_folder")
        dl_folder = Path(artifacts_folder).parents[0] / "d"

        # FIXME: refactor all this part
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
                        artifact_info.update({"name": file_name, "path": f'{remote_path}/{file_name}'})
                    else:
                        ref = node.get("ref")
                        pkg = f":{node.get('package_id')}:{node.get('prev')}" if artifact_type == "package" else ""
                        artifact_info.update({"id": f"{ref}{pkg}::{file_name}"})

                    artifacts.append(artifact_info)

        if not artifacts:
            # we don't have the artifacts in the local cache
            # it's possible that the packages came from an install without a build
            # so let's ask Artifactory about the checksums of the packages
            # we can use the Conan API to get the enabled remotes and iterate through them
            # but it may be better to use a specific repo when creating the build info ?
            assert self._url and self._repositories, "Missing information in the Conan local cache, " \
                                                     "please provide the --url and --repository arguments " \
                                                     "to retrieve the information from Artifactory."
            for repository in self._repositories:
                # change from the conan API to the correct API to get files info and ignore if
                # this can lead to problems, probably is better to pass manually a list of URLs
                for artifact in artifacts_names:
                    request_url = f"{self._url}/api/storage/{repository}/{remote_path}/{artifact}"
                    if not self._cached_artifact_info.get(request_url):
                        checksums = None
                        try:
                            response = api_request("get", request_url, self._user, self._password, self._apikey)
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

                        if not is_dependency:
                            artifact_info.update({"name": artifact, "path": f'{remote_path}/{artifact}'})
                        else:
                            ref = node.get("ref")
                            pkg = f":{node.get('package_id')}:{node.get('prev')}" if artifact_type == "package" else ""
                            artifact_info.update({"id": f"{ref}{pkg}::{artifact}"})

                        artifacts.append(artifact_info)
                    else:
                        break
                if artifacts:
                    break

        if not artifacts:
            raise ConanException(f"There are no artifacts for the {node.get('ref')} {artifact_type}. " \
                                 "Probably the package was not uploaded before creating the Build Info." \
                                 "Please upload the package to the server and try again.")
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
                    requires = node.get("requires")
                    # recipe module
                    module = {
                        "type": "conan",
                        "id": str(ref),
                        "artifacts": self.get_artifacts(node, "recipe")
                    }

                    all_dependencies = []
                    for require_id in unique_reqs:
                        all_dependencies.extend(
                            self.get_artifacts(get_node_by_id(nodes, require_id), "recipe", is_dependency=True))

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
                        all_dependencies = []
                        for require_id in unique_reqs:
                            all_dependencies.extend(
                                self.get_artifacts(get_node_by_id(nodes, require_id), "package", is_dependency=True))

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

    subparser.add_argument("--url", help="Artifactory url, like: https://<address>/artifactory. "
                                         "This may be not necessary if all the information for the Conan "
                                         "artifacts is present in the local cache.")

    subparser.add_argument("--repository", help="Repositories to look artifacts for."
                                                "This may be not necessary if all the information for the Conan "
                                                "artifacts is present in the local cache."
                           , action="append")

    subparser.add_argument("--user", help="user name for the repository")
    subparser.add_argument("--password", help="password for the user name")
    subparser.add_argument("--apikey", help="apikey for the repository")

    args = parser.parse_args(*args)

    with open(args.json, 'r') as f:
        data = json.load(f)

    bi = BuildInfo(data, args.build_name, args.build_number, args.repository, args.url, args.user, args.password,
                   args.apikey)

    cli_out_write(bi.create())


@conan_subcommand()
def build_info_upload(conan_api: ConanAPI, parser, subparser, *args):
    """
    Uploads BuildInfo json to repository.
    """

    subparser.add_argument("build_info", help="BuildInfo json file.")
    subparser.add_argument("url", help="Artifactory url, like: https://<address>/artifactory")

    subparser.add_argument("--user", help="user name for the repository")
    subparser.add_argument("--password", help="password for the user name")
    subparser.add_argument("--apikey", help="apikey for the repository")
    args = parser.parse_args(*args)

    with open(args.build_info) as f:
        build_info_json = json.load(f)

    request_url = f"{args.url}/api/build"
    response = api_request("put", request_url, args.user, args.password,
                           args.apikey, json_data=json.dumps(build_info_json))
    cli_out_write(response)


@conan_subcommand()
def build_info_promote(conan_api: ConanAPI, parser, subparser, *args):
    """
    Promote the BuildInfo from the source to the target repository.
    """

    subparser.add_argument("build_name", help="BuildInfo name to promote.")
    subparser.add_argument("build_number", help="BuildInfo number to promote.")
    subparser.add_argument("url", help="Artifactory url, like: https://<address>/artifactory")
    subparser.add_argument("source_repo", help="Source repo for promotion.")
    subparser.add_argument("target_repo", help="Target repo for promotion.")

    subparser.add_argument("--dependencies", help="Whether to copy the build's dependencies or not. Default: false.",
                           action='store_true', default=False)
    subparser.add_argument("--comment", help="An optional comment describing the reason for promotion. Default: ''")

    subparser.add_argument("--user", help="user name for the repository")
    subparser.add_argument("--password", help="password for the user name")
    subparser.add_argument("--apikey", help="apikey for the repository")

    args = parser.parse_args(*args)

    promotion_json = {
        "sourceRepo": args.source_repo,
        "targetRepo": args.target_repo,
        # Conan promotions must always be copy, and the clean must be handled manually
        # otherwise you can end up deleting recipe artifacts that other packages use
        "copy": "true",
        "dependencies": "true" if args.dependencies else "false",
        "comment": args.comment
    }

    request_url = f"{args.url}/api/build/promote/{args.build_name}/{args.build_number}"

    response = api_request("post", request_url, args.user, args.password, args.apikey,
                           json_data=json.dumps(promotion_json))

    cli_out_write(response)


@conan_subcommand()
def build_info_get(conan_api: ConanAPI, parser, subparser, *args):
    """
    Get Build Info information.
    """

    subparser.add_argument("build_name", help="BuildInfo name to get.")
    subparser.add_argument("build_number", help="BuildInfo number to get.")
    subparser.add_argument("url", help="Artifactory url, like: https://<address>/artifactory")

    subparser.add_argument("--user", help="user name for the repository")
    subparser.add_argument("--password", help="password for the user name")
    subparser.add_argument("--apikey", help="apikey for the repository")

    args = parser.parse_args(*args)

    request_url = f"{args.url}/api/build/{args.build_name}/{args.build_number}"

    response = api_request("get", request_url, args.user, args.password, args.apikey)

    cli_out_write(response)


@conan_subcommand()
def build_info_delete(conan_api: ConanAPI, parser, subparser, *args):
    """
    Removes builds stored in Artifactory. Useful for cleaning up old build info data.
    """

    subparser.add_argument("build_name", help="BuildInfo name to delete.")
    subparser.add_argument("url", help="Artifactory url, like: https://<address>/artifactory")

    subparser.add_argument("--build-number", help="BuildInfo numbers to promote. You can add " \
                                                  "several build-numbers for the same build-name, like: --build-number=1 --build-number=2.",
                           action='append')

    subparser.add_argument("--delete-artifacts", help="Build artifacts are also removed " \
                                                      "provided they have the corresponding build.name and build.number properties attached to them. " \
                                                      "Default false.",
                           action='store_true', default=False, )
    subparser.add_argument("--delete-all", help="The whole build is removed. Default false.",
                           action='store_true', default=False, )

    subparser.add_argument("--user", help="user name for the repository")
    subparser.add_argument("--password", help="password for the user name")
    subparser.add_argument("--apikey", help="apikey for the repository")

    args = parser.parse_args(*args)

    delete_json = {
        "buildName": args.build_name,
        "buildNumbers": args.build_number,
        "deleteArtifacts": "true" if args.delete_artifacts else "false",
        "deleteAll": "true" if args.delete_all else "false",
    }

    request_url = f"{args.url}/api/build/delete"

    response = api_request("post", request_url, args.user, args.password, args.apikey,
                           json_data=json.dumps(delete_json))

    cli_out_write(response)


@conan_subcommand()
def build_info_append(conan_api: ConanAPI, parser, subparser, *args):
    """
    Append published build to the build info.
    """

    subparser.add_argument("build_name", help="The current build name.")
    subparser.add_argument("build_number", help="The current build number.")

    subparser.add_argument("--build-info", help="JSON file for the Build Info. You can add multiple files " \
                                                "like --build-info=release.json --build-info=debug.json",
                           action="append")

    args = parser.parse_args(*args)

    all_modules = []

    for build_info_json in args.build_info:
        with open(build_info_json, 'r') as f:
            data = json.load(f)
            for module in data.get("modules"):
                # avoid repeating shared recipe modules between builds
                if not any(d['id'] == module.get('id') for d in all_modules):
                    all_modules.append(module)

    bi = BuildInfo(None, args.build_name, args.build_number)
    bi_json = bi.header()
    bi_json.update({"modules": all_modules})
    cli_out_write(json.dumps(bi_json, indent=4))
