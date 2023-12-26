import os
import json
from conan.api.conan_api import ConanAPI
from conan.api.output import ConanOutput, cli_out_write
from conan.cli.command import conan_command, conan_subcommand

from utils import assert_server_or_url_user_password
from cmd_server import get_url_user_password
from cmd_generic_repo import read_file, upload_file, list_folders


report_template = {
    "build_status": None,
    "build_log": None,
    "build_profile_build": None,
    "build_profile_host": None,
    "test_status": None,
    "test_log": None,
    "test_profile_build": None,
    "test_profile_host": None
}

def save(f, content):
    with open(f, "w") as f:
        f.write(content)


def output_json(exported_refs):
    cli_out_write(json.dumps(exported_refs["exported_references"].serialize(), indent=1))


def output_text(exported_refs):
    ConanOutput().title("Exported references")
    for ref in exported_refs["exported_references"]["Local Cache"].refs():
        cli_out_write(f"{ref.name}/{ref.version}#{ref.revision}")


@conan_command(group="Artifactory")
def build_report(conan_api: ConanAPI, parser, *args):
    """
    Manages build logs from Conan builds, generates a report and uploads it to a Generic repository in Artifactory.
    """


@conan_subcommand()
def build_report_add(conan_api: ConanAPI, parser, subparser, *args):
    """
    Export all versions of recipe in conan-center-index, given a path. Optionally, export only the most recent version.
    [PR_NUMBER]/[BUILD_NUMBER]/<ref#rrev>-<profile_build>-<profile_host>/report.json --> status, build_log (paths)
    [PR_NUMBER]/[BUILD_NUMBER]/<ref#rrev>-<profile_build>-<profile_host>/build_log.txt
    [PR_NUMBER]/[BUILD_NUMBER]/<ref#rrev>-<profile_build>-<profile_host>/test_log.txt
    [PR_NUMBER]/[BUILD_NUMBER]/<ref#rrev>-<profile_build>-<profile_host>/profile_build.txt (effective profile)
    [PR_NUMBER]/[BUILD_NUMBER]/<ref#rrev>-<profile_build>-<profile_host>/profile_host.txt (effective profile)
    [PR_NUMBER]/[BUILD_NUMBER]/<ref#rrev>-<profile_build>-<profile_host>/test_profile_build.txt (effective profile)
    [PR_NUMBER]/[BUILD_NUMBER]/<ref#rrev>-<profile_build>-<profile_host>/test_profile_host.txt (effective profile)
    """

    subparser.add_argument("pull_request_number", help="Pull-request number")
    subparser.add_argument("build_number", help="Number of the build")
    subparser.add_argument("id", help="ID of the report")
    subparser.add_argument("repository", help="Artifactory repo to store the report")
    subparser.add_argument("--build_status", help="Status of the build")
    subparser.add_argument("--build_log", help="path to the build log file")
    subparser.add_argument("--profile_build", help="path to the profile build file")
    subparser.add_argument("--profile_host", help="path to the profile host file")
    subparser.add_argument("--test_status", help="Status of the build")
    subparser.add_argument("--test_log", help="path to the test log file")
    subparser.add_argument("--test_profile_build", help="path to the profile build file")
    subparser.add_argument("--test_profile_host", help="path to the profile host file")
    subparser.add_argument("--server", help="Server name of the Artifactory to get the build info from")
    subparser.add_argument("--url", help="Artifactory url, like: https://<address>/artifactory")
    subparser.add_argument("--user", help="user name for the repository")
    subparser.add_argument("--password", help="password for the user name")
    
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

    for field in ["build_status", "build_log", "build_profile_build", "build_profile_host",
                  "test_status", "test_log", "test_profile_build", "test_profile_host"]:
        field_value = vars(args).get(field)
        if field_value:
            if "status" in field:
                report[field] = field_value
            else:
                report[field] = f"{base_path}/{field_value}"
    save("report.json", json.dumps(report))

    for key, value in report.items():
        if "status" not in key and value:
            upload_file(args.repository, os.path.basename(value), base_path, url, user, password)
    upload_file(args.repository, "report.json", base_path, url, user, password)


@conan_subcommand()
def build_report_summary(conan_api: ConanAPI, parser, subparser, *args):
    """
    lllllllllllllllll
    """

    subparser.add_argument("pull_request_number", help="Pull-request number")
    subparser.add_argument("build_number", help="Number of the build")
    subparser.add_argument("repository", help="Artifactory repo to store the report")
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
