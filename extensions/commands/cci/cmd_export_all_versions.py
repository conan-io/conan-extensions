import os
import json
import textwrap
import yaml

from conan.api.output import ConanOutput, cli_out_write
from conan.cli.command import conan_command, OnceArgument
from conan.errors import ConanException


def output_json(result):
    cli_out_write(json.dumps({
        "exported": [repr(r) for r in result['exported']],
        "failures": result['failures']
    }))

def output_text(result):
    exported = result["exported"]
    failed = result["failures"]
    exported_with_revision = result["exported_with_revisions"]
    versions_list = result["exported_with_versions"]

    cli_out_write("EXPORTED RECIPES")
    for item in exported.keys():
        cli_out_write(f"{item}: exported {len(exported[item])} versions")

    cli_out_write("FAILED TO EXPORT")
    for key, value in failed.items():
        cli_out_write(f"{key}, {value}")

    cli_out_write("RECIPE REFERENCES")
    for item in exported_with_revision:
        cli_out_write(f"{item}")

    cli_out_write("VERSION LIST")
    cli_out_write(f'{versions_list}')



def output_markdown(result):
    exported = result['exported']
    failures = result['failures']
    print(textwrap.dedent(f"""
    ### Conan Export Results

    Successfully exported {sum([len(versions) for versions in exported.values()])} versions from {len(exported.keys())} recipes while encountering {len(failures)} recipes that could not be exported; these are


    <table>
    <th>
    <td> Recipe </td> <td> Reason </td>
    </th>"""))

    for key, value in failures.items():
        print(textwrap.dedent(f"""
            <tr>
            <td> {key} </td>
            <td>

            ```txt
            """))
        print(f"{value}")
        print(textwrap.dedent(f"""
            ```

            </td>
            </tr>
            """))

    print("</table>")


@conan_command(group="Conan Center Index", formatters={"text": output_text, "json": output_json, "md": output_markdown})
def export_all_versions(conan_api, parser, *args):
    """
    Export all version of either a single recipe, a list of recipes, or a global recipes folder
    """
    group = parser.add_mutually_exclusive_group()
    group.add_argument('-n', '--name', action=OnceArgument, help="Name of the recipe to export. This will export only one recipe.")
    group.add_argument('-l', '--list', action=OnceArgument, help="YAML file with list of recipes to export. All the recipes on the list will be exported")
    group.add_argument('-p', '--path', action=OnceArgument, help="Path of the global recipe folder. This will export all recipes in that folder")
    args = parser.parse_args(*args)

    if args.name is not None:
        recipes_to_export = [args.name]
    elif args.list is not None:
        recipes_to_export = yaml.safe_load(open(args.list, 'r'))["recipes"]
    else:
        recipes_to_export = os.listdir(args.path)

    out = ConanOutput()

    # Result output variables, these should always be returned
    exported = {}
    exported_refs = []
    exported_with_revision = []
    failed = dict()

    for item in recipes_to_export:
        recipe_name = item if not isinstance(item, dict) else list(item.keys())[0]
        folders_to_export = item[recipe_name][0]['folders'] if isinstance(item, dict) else None
        out.verbose(f"Processing recipe '{recipe_name}'")

        recipe_folder = os.path.join(args.path, recipe_name)
        if not os.path.isdir(recipe_folder):
            raise ConanException(f"Invalid user input: '{recipe_name}' does not exist or is not a dir")

        config_file = os.path.join(recipe_folder, "config.yml")
        if not os.path.isfile(config_file):
            out.error(f"The file {config_file} does not exist")
            failed[recipe_name] = "no config.yml"
            continue

        config = yaml.safe_load(open(config_file, "r"))
        for version in config["versions"]:
            recipe_subfolder = config["versions"][version]["folder"]
            if folders_to_export and recipe_subfolder not in folders_to_export:
                continue
            conanfile = os.path.join(recipe_folder, recipe_subfolder, "conanfile.py")
            if not os.path.isfile(conanfile):
                raise ConanException(f"The file {conanfile} does not exist")

            out.verbose(f"Exporting {recipe_name}/{version} from {recipe_subfolder}/")
            try:
                ref = conan_api.export.export(os.path.abspath(conanfile), recipe_name, version, None, None)
                out.verbose(f"Exported {ref}")

                if recipe_name not in exported:
                    exported[recipe_name] = []
                exported[recipe_name].append(ref)
                exported_refs.append(ref)

                exported_with_revision.append(f"{ref[0].name}/{ref[0].version}#{ref[0].revision}")
            except Exception as e:
                failed.update({f"{recipe_name}/{recipe_subfolder}": str(e)})

    return {"exported": exported,
            "failures": failed,
            "exported_with_revisions": exported_with_revision,
            "exported_with_versions": [f"{item[1]}" for item in exported_refs]}
