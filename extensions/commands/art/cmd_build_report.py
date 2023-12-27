import os
import json
from conan.api.conan_api import ConanAPI
from conan.api.output import cli_out_write
from conan.cli.command import conan_command, conan_subcommand

from utils import assert_server_or_url_user_password, load_json
from cmd_server import get_url_user_password
from cmd_generic_repo import read_file, upload_file, list_folders


report_template = {
    "reference": None,
    "settings": {},
    "options": {},
    "package_id": None,
    "build_status": None,
    "build_log": None,
    "test_status": None,
    "test_log": None,
}

def save(f, content):
    with open(f, "w") as f:
        f.write(content)


@conan_command(group="Artifactory")
def build_report(conan_api: ConanAPI, parser, *args):
    """
    Manages build logs from Conan builds, generates a report or a summary and uploads it to a Generic repository in Artifactory.
    """


@conan_subcommand()
def build_report_add(conan_api: ConanAPI, parser, subparser, *args):
    """
    Generate a build report by adding information of the build for a pull-request, build and ID.
    The report will be stored in the specified generic repository in Artifactory following the structure:
        <repository>/<pull_request_number>/<build_number>/<id>/build_log.txt|test_log.txt|report.json --> reference, settings, options, package_id, build_status, test_status
    """

    subparser.add_argument("repository", help="Artifactory repo to store the report")
    subparser.add_argument("pull_request_number", help="Pull-request number")
    subparser.add_argument("build_number", help="Number of the build")
    subparser.add_argument("id", help="ID of the report")
    subparser.add_argument("--graph_info_json", help="Graph info of the build in JSON format")
    subparser.add_argument("--build_status", help="Status of the build")
    subparser.add_argument("--build_log", help="Path to the build log file")
    subparser.add_argument("--test_status", help="Status of the test")
    subparser.add_argument("--test_log", help="Path to the test log file")
    subparser.add_argument("--server", help="Server name of the Artifactory to get the build info from")
    subparser.add_argument("--url", help="Artifactory url, like: https://<address>/artifactory")
    subparser.add_argument("--user", help="User for Artifactory credentials")
    subparser.add_argument("--password", help="Password for Artifactory credentials")
    
    args = parser.parse_args(*args)
    pr_number = args.pull_request_number
    build_number = args.build_number
    id = args.id
    base_path = f"{pr_number}/{build_number}/{id}"

    assert_server_or_url_user_password(args)
    url, user, password = get_url_user_password(args)

    report = report_template.copy()
    try:
        content = read_file(args.repository, f"{base_path}/report.json", url, user, password)
        report = json.loads(content)
    except Exception:
        pass

    for field in ["build_status", "build_log", "test_status", "test_log", "graph_info_json"]:
        field_value = vars(args).get(field)
        if field_value:
            if "status" in field:
                report[field] = field_value
            elif "graph_info_json" in field:
                graph_info = load_json(field_value)
                report["reference"] = graph_info["graph"]["nodes"]["1"].get("ref")
                report["settings"] = graph_info["graph"]["nodes"]["1"].get("settings")
                report["options"] = graph_info["graph"]["nodes"]["1"].get("options")
                report["package_id"] = graph_info["graph"]["nodes"]["1"].get("package_id")
            else:
                report[field] = f"{base_path}/{field_value}"
    save("report.json", json.dumps(report))

    for key, value in report.items():
        if "log" in key and value:
            upload_file(args.repository, os.path.basename(value), base_path, url, user, password)
    upload_file(args.repository, "report.json", base_path, url, user, password)
    cli_out_write(f"Report:\n{json.dumps(report, indent=4)}")


@conan_subcommand()
def build_report_summary(conan_api: ConanAPI, parser, subparser, *args):
    """
    Collect build reports from same pull-request number and build and store them together in a common file.
    The summary will be stored in a generic repository in Artifactory following the structure:
        <repository>/<pull_request_number>/<build_number>/summary.json
    """

    subparser.add_argument("repository", help="Artifactory repo to store the report")
    subparser.add_argument("pull_request_number", help="Pull-request number")
    subparser.add_argument("build_number", help="Number of the build")
    subparser.add_argument("--server", help="Server name of the Artifactory to get the build info from")
    subparser.add_argument("--url", help="Artifactory url, like: https://<address>/artifactory")
    subparser.add_argument("--user", help="user name for the repository")
    subparser.add_argument("--password", help="password for the user name")

    args = parser.parse_args(*args)

    assert_server_or_url_user_password(args)
    url, user, password = get_url_user_password(args)
    path = f"{args.pull_request_number}/{args.build_number}"
    folders = list_folders(args.repository, path, url, user, password)
    summary_data = []
    for folder in folders:
        content = read_file(args.repository, f"{path}/{folder}/report.json", url, user, password)
        report_data = json.loads(content)
        summary_data.append(report_data)
    save("summary.json", json.dumps(summary_data))
    upload_file(args.repository, "summary.json", path, url, user, password)
    cli_out_write(f"Summary:\n{json.dumps(summary_data, indent=4)}")
