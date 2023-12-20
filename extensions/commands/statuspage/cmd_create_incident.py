import requests
from conan.cli.command import conan_command
from conan.api.conan_api import ConanAPI
from conan.errors import ConanException
from conan.api.output import cli_out_write
from statuspage_utils import get_token, output_json, add_common_arguments
from statuspage_requester import post


__version__ = "0.1.0"


def output_text(results: dict):
    lines = [f"Incident ID: {results['id']}", f"Created at: {results['created_at']}", f"Name: {results['name']}",
             f"Status: {results['status']}", f"Impact: {results['impact']}", f"URL: {results['shortlink']}"]
    cli_out_write("Created incident:\n{}\n".format('\n'.join(lines)))


@conan_command(group="Status Page", formatters={"json": output_json, "text": output_text})
def create_incident(conan_api: ConanAPI, parser, *args) -> dict:
    """
    Create a new incident in Status Page.

    https://developer.statuspage.io/#operation/postPagesPageIdIncidents
    """
    add_common_arguments(parser)
    parser.add_argument("-t", "--title", type=str, help="Incident title")
    parser.add_argument("-m", "--message", type=str, help="Incident body description")
    parser.add_argument("-s", "--status", help="Incident status", choices=["investigating", "identified", "monitoring", "resolved"])
    parser.add_argument("-i", "--impact", help="Incident impact", choices=["none", "maintenance", "minor", "major", "critical"])
    parser.add_argument("-cs", "--component-status", help="Component status", choices=["operational", "degraded_performance", "partial_outage", "major_outage"])
    parser.add_argument('-c', "--components", help="Incident components", nargs="+")
    args = parser.parse_args(*args)

    token = get_token(args)
    if not token:
        raise ConanException("Status Page API token is required.")
    if not args.page:
        raise ConanException("Status Page ID is required.")
    if not args.title:
        raise ConanException("Incident title is required.")

    comp_status = args.component_status or 'major_outage'
    payload = {"incident": {"name": args.title}}
    if args.status:
        payload["incident"]["status"] = args.status
    if args.message:
        payload["incident"]["body"] = args.message
    if args.component_status:
        payload["incident"]["components"] = {component: comp_status for component in args.components}
        payload["incident"]["component_ids"] = args.components
    if args.impact:
        payload["incident"]["impact_override"] = args.impact
    return post(f"pages/{args.page}/incidents", token, payload, verify=not args.ignore_ssl)
