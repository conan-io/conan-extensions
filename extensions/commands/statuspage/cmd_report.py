# import requests
# import platform
# from argparse import ArgumentParser
# import subprocess
# import getpass
# import json
# from datetime import datetime, timezone, timedelta
# from conan.cli.command import conan_command, conan_subcommand
# from conan.api.conan_api import ConanAPI
# from conan.api.output import ConanOutput, cli_out_write
# from conan.errors import ConanException
#
#
# __version__ = "0.1.0"
#
#
# def get_token(args):
#     token = args.token
#     if not args.token and platform.system() == "Darwin":
#         # INFO: https://scriptingosx.com/2021/04/get-password-from-keychain-in-shell-scripts/
#         # security add-generic-password -s 'CLI Test'  -a 'armin' -w 'password123'
#         # security find-generic-password -w -s 'CLI Test' -a 'armin'
#         user = args.user or getpass.getuser()
#         print(f"Getting Status Page token from keychain for user '{user}'")
#         output = subprocess.run(["security", "find-generic-password", "-a", user, "-s", args.service, "-w"], capture_output=True, text=True)
#         token = output.stdout.strip()
#     return token
#
# def output_json(results):
#     print(json.dumps(results, indent=2))
#
@conan_command(group="Status Page", formatters={"json": output_json})
def report(conan_api: ConanAPI, parser, *args):
    """
    Manage Status Page incidents.
    """
    pass
#
#
# @conan_subcommand()
# def report_create_incident(conan_api: ConanAPI, parser, subparser, *args):
#     """
#     Create a new incident in Status Page.
#     https://developer.statuspage.io/#operation/postPagesPageIdIncidents
#     """
#     subparser.add_argument("-tk", "--token", type=str, help="Status Page API token")
#     subparser.add_argument("-t", "--title", type=str, help="Incident title")
#     subparser.add_argument("-m", "--message", type=str, help="Incident body description")
#     subparser.add_argument("-s", "--status", help="Incident status", choices=["investigating", "identified", "monitoring", "resolved"])
#     subparser.add_argument("-i", "--impact", help="Incident impact", choices=["none", "maintenance", "minor", "major", "critical"])
#     subparser.add_argument("-cs", "--component-status", help="Component status", choices=["operational", "degraded_performance", "partial_outage", "major_outage"])
#     subparser.add_argument("-p", "--page", type=str, help="Status Page ID")
#     subparser.add_argument('-c', "--components", help="Incident components", nargs="+")
#     subparser.add_argument('-g', '--ignore-ssl', action='store_true', help="Ignore SSL verification")
#     subparser.add_argument('-ku', '--keychain-user', type=str, help="Status Page username")
#     subparser.add_argument("-ks", "--keychain-service", type=str, help="Keychain service", default="statuspage-token")
#     args = parser.parse_args(*args)
#
#     token = get_token(args)
#     if not token:
#         raise ConanException("Status Page API token is required.")
#     if not args.page:
#         raise ConanException("Status Page ID is required.")
#     if not args.title:
#         raise ConanException("Incident title is required.")
#
#     output = ConanOutput()
#     url = f"https://api.statuspage.io/v1/pages/{args.page}/incidents"
#     comp_status = args.component_status or 'major_outage'
#     payload = {"incident": {"name": args.title}}
#     if args.status:
#         payload["incident"]["status"] = args.status
#     if args.message:
#         payload["incident"]["body"] = args.message
#     if args.component_status:
#         payload["incident"]["components"] = {component: comp_status for component in args.components}
#         payload["incident"]["component_ids"] = args.components
#     if args.impact:
#         payload["incident"]["impact_override"] = args.impact
#     output.info(f"Creating a new incident: {args.title}")
#     headers = {"Authorization": f"OAuth {token}", "Content-Type": "application/json"}
#     response = requests.post(url, json=payload, headers=headers, verify=not args.ignore_ssl)
#     response.raise_for_status()
#     output.info(f"Status Page API response ({response.status_code}):\n{response.json()}")
