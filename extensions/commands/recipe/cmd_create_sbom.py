import os.path
import sys
from typing import TYPE_CHECKING, Any, Iterable, List, Optional, Set, Tuple, Union, Dict

from conan.api.conan_api import ConanAPI
from conan.api.output import cli_out_write
from conan.cli.args import common_graph_args, validate_common_graph_args
from conan.cli.command import conan_command

if TYPE_CHECKING:
    from cyclonedx.model.bom import Bom


def format_text(output: Dict[str, Any]) -> None:
    serialized = output['formatters'][output['sbom_format']](output['bom']).output_as_string()
    cli_out_write(serialized)


@conan_command(group="Recipe", formatters={"text": format_text})
def create_sbom(conan_api: ConanAPI, parser, *args) -> Dict[str, Any]:
    """Create a CycloneDX Software Bill of Materials (SBOM)"""

    try:
        from cyclonedx.factory.license import LicenseFactory
        from cyclonedx.model import (ExternalReference, ExternalReferenceType,
                                     LicenseChoice, Tool, XsUri)
        from cyclonedx.model.bom import Bom
        from cyclonedx.model.component import Component, ComponentType
        import cyclonedx.output.json
        import cyclonedx.output.xml
        from packageurl import PackageURL
    except ModuleNotFoundError:
        # Assert on RUNTIME of the actual conan-command, that all requirements exist.
        # Since conan loads all extensions when started, this check could prevent conan from running,
        # if loading dependencies is performed outside the actual conan-command in global/module scope.
        print('The sbom extension needs an additional package, please run:',
              # keep in synk with the instructions in `README.md`
              "pip install 'cyclonedx-python-lib>=4.0.1,<5.0.0'",
              sep='\n', file=sys.stderr)
        sys.exit(1)

    if TYPE_CHECKING:
        from conans.client.graph.graph import Node

    def package_type_to_component_type(pt: str) -> ComponentType:
        return ComponentType.APPLICATION if pt == "application" else ComponentType.LIBRARY

    def licenses(ls: Optional[Union[Tuple[str, ...], Set[str], List[str], str]]) -> Optional[Iterable[LicenseChoice]]:
        """
        see https://cyclonedx.org/docs/1.4/json/#components_items_licenses
        """
        if ls is None:
            return None
        if not isinstance(ls, (tuple, set, list)):
            ls = [ls]
        return [LicenseChoice(license=LicenseFactory().make_from_string(i)) for i in ls]

    def package_url(node: 'Node') -> Optional[PackageURL]:
        """
        Creates a PURL following https://github.com/package-url/purl-spec/blob/master/PURL-TYPES.rst#conan
        """
        return PackageURL(
            type="conan",
            name=node.name,
            version=node.conanfile.version,
            qualifiers={
                "prev": node.prev,
                "rref": node.ref.revision if node.ref else None,
                "user": node.conanfile.user,
                "channel": node.conanfile.channel,
                "repository_url": node.remote.url if node.remote else None
            }
        ) if node.name else None

    def create_component(node: 'Node') -> Component:
        purl = package_url(node)
        component = Component(
            type=package_type_to_component_type(node.conanfile.package_type),
            name=node.name or f'UNKNOWN.{id(node)}',
            version=node.conanfile.version,
            licenses=licenses(node.conanfile.license),
            bom_ref=purl.to_string() if purl else None,
            purl=purl,
            description=node.conanfile.description
        )
        if node.conanfile.homepage:
            component.external_references.add(ExternalReference(
                type=ExternalReferenceType.WEBSITE,
                url=XsUri(node.conanfile.homepage),
            ))
        return component

    def me_as_tool() -> Tool:
        tool = Tool(name="conan extension recipe:create-sbom")
        tool.external_references.add(ExternalReference(
            type=ExternalReferenceType.WEBSITE,
            url=XsUri("https://github.com/conan-io/conan-extensions")))
        return tool

    formatters = {
        '1.4_json': cyclonedx.output.json.JsonV1Dot4,
        '1.3_json': cyclonedx.output.json.JsonV1Dot3,
        '1.2_json': cyclonedx.output.json.JsonV1Dot2,
        '1.4_xml': cyclonedx.output.xml.XmlV1Dot4,
        '1.3_xml': cyclonedx.output.xml.XmlV1Dot3,
        '1.2_xml': cyclonedx.output.xml.XmlV1Dot2,
        '1.1_xml': cyclonedx.output.xml.XmlV1Dot1,
        '1.0_xml': cyclonedx.output.xml.XmlV1Dot0
    }
    parser.add_argument("--sbom_format", choices=formatters.keys(), required=True)

    # region COPY FROM conan: cli/commands/graph.py
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
    # endregion COPY

    components = {node: create_component(node) for node in deps_graph.nodes}
    bom = Bom()
    bom.metadata.component = components[deps_graph.root]
    bom.metadata.tools.add(me_as_tool())
    for node in deps_graph.nodes[1:]:  # node 0 is the root
        bom.components.add(components[node])
    for dep in deps_graph.nodes:
        bom.register_dependency(components[dep], [components[dep_dep.dst] for dep_dep in dep.dependencies])
    return {'bom': bom, 'sbom_format': args.sbom_format, 'formatters': formatters}
