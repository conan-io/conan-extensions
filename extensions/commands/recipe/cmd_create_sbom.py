import os.path

from packageurl import PackageURL
from cyclonedx.factory.license import LicenseFactory
from cyclonedx.model import ExternalReference, ExternalReferenceType, LicenseChoice, XsUri
from cyclonedx.model.bom import Bom
from cyclonedx.model.component import Component, ComponentType
from cyclonedx.output.json import JsonV1Dot4

from conan.api.output import cli_out_write
from conan.api.conan_api import ConanAPI
from conan.cli.args import common_graph_args, validate_common_graph_args
from conan.cli.command import conan_command
from conans.client.graph.graph import Node

lFac = LicenseFactory()
unknown_name_created = False


def package_type_to_component_type(pt: str) -> ComponentType:
    if pt is "application":
        return ComponentType.APPLICATION
    else:
        return ComponentType.LIBRARY


def licenses(ids):
    """
    see https://cyclonedx.org/docs/1.4/json/#components_items_licenses
    """
    if ids is None:
        return None
    if not isinstance(ids, tuple):
        ids = [ids]
    return [LicenseChoice(license=lFac.make_from_string(i)) for i in ids]


def name(n: Node) -> str:
    if n.name:
        return n.name
    else:
        assert globals()["unknown_name_created"] is False, "multiple nodes have no name"
        globals()["unknown_name_created"] = True
        return "UNKNOWN"


def package_url(node: Node, name: str) -> PackageURL:
    """
    Creates a PURL following https://github.com/package-url/purl-spec/blob/master/PURL-TYPES.rst#conan
    """
    return PackageURL(
        type="conan",
        name=name,
        version=node.conanfile.version,
        qualifiers={
            "prev": node.prev,
            "rref": node.ref.revision if node.ref else None,
            "user": node.conanfile.user,
            "channel": node.conanfile.channel,
            "repository_url": node.remote.url if node.remote else None
        })


def create_component(n: Node) -> Component:
    name_ = name(n)
    purl = package_url(n, name_)
    result = Component(
        type=package_type_to_component_type(n.conanfile.package_type),
        name=name_,
        version=n.conanfile.version,
        licenses=licenses(n.conanfile.license),
        bom_ref=purl.to_string(),
        purl=purl,
        description=n.conanfile.description
    )
    if n.conanfile.homepage:
        result.external_references.add(ExternalReference(
            type=ExternalReferenceType.WEBSITE,
            url=XsUri(n.conanfile.homepage),
        ))
    return result


@conan_command(group="Recipe")
def create_sbom(conan_api: ConanAPI, parser, *args):
    """
    creates an SBOM in CycloneDX 1.4 JSON format
    """

    # BEGIN COPY FROM conan: cli/commands/graph.py
    common_graph_args(parser)
    args = parser.parse_args(*args)
    validate_common_graph_args(args)
    cwd = os.getcwd()
    path = conan_api.local.get_conanfile_path(args.path, cwd, py=None) if args.path else None
    remotes = conan_api.remotes.list(args.remote) if not args.no_remote else []
    overrides = eval(args.lockfile_overrides) if args.lockfile_overrides else None
    lockfile = conan_api.lockfile.get_lockfile(lockfile=args.lockfile,
                                               conanfile_path=path,
                                               cwd=cwd,
                                               partial=args.lockfile_partial,
                                               overrides=overrides)
    profile_host, profile_build = conan_api.profiles.get_profiles_from_args(args)
    if path:
        deps_graph = conan_api.graph.load_graph_consumer(path, args.name, args.version,
                                                     args.user, args.channel,
                                                     profile_host, profile_build, lockfile,
                                                     remotes, args.update)
    else:
        deps_graph = conan_api.graph.load_graph_requires(args.requires, args.tool_requires,
                                                         profile_host, profile_build, lockfile,
                                                         remotes, args.update)
    # END COPY
    globals()["unknown_name_created"] = False
    components = {n: create_component(n) for n in deps_graph.nodes}
    bom = Bom()
    bom.metadata.component = components[deps_graph.root]
    for n in deps_graph.nodes[1:]:  # node 0 is the root
        bom.components.add(components[n])
    for dep in deps_graph.nodes:
        bom.register_dependency(components[dep], [components[dep_dep.dst] for dep_dep in dep.dependencies])
    serialized_json = JsonV1Dot4(bom).output_as_string()
    cli_out_write(serialized_json)
