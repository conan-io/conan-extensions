import requests
from conan.cli.command import conan_command
from conan.api.conan_api import ConanAPI
from conan.api.output import cli_out_write
from conan.errors import ConanException
from statuspage_utils import get_token, output_json
from statuspage_requester import Requester


__version__ = "0.1.0"


def output_text(results: dict):
    lines = [f"Incident ID: {results['id']}", f"Created at: {results['created_at']}",  f"Updated at: {results['updated_at']}", f"Name: {results['name']}",
             f"Status: {results['status']}", f"Impact: {results['impact']}", f"URL: {results['shortlink']}"]
    cli_out_write("Resolved incident:\n{}\n".format('\n'.join(lines)))


@conan_command(group="Status Page", formatters={"json": output_json, "text": output_text})
def resolve_incident(conan_api: ConanAPI, parser, *args) -> dict:
    """
    Resolve an existing incident in Status Page.

    https://developer.statuspage.io/#operation/patchPagesPageIdIncidentsIncidentId
    """
    parser.add_argument("-tk", "--token", type=str, help="Status Page API token")
    parser.add_argument("-ic", "--incident", type=str, help="Existing incident ID")
    parser.add_argument('-e', '--event', help="Event type to be finished", choices=["maintenance", "incident"])
    parser.add_argument("-p", "--page", type=str, help="Status Page ID")
    parser.add_argument('-c', "--components", help="Incident components", nargs="+")
    parser.add_argument("-m", "--message", type=str, help="Incident body description")
    parser.add_argument('-g', '--ignore-ssl', action='store_true', help="Ignore SSL verification")
    parser.add_argument('-ku', '--keychain-user', type=str, help="Status Page username")
    parser.add_argument("-ks", "--keychain-service", type=str, help="Keychain service", default="statuspage-token")
    args = parser.parse_args(*args)

    token = get_token(args)
    if not token:
        raise ConanException("Status Page API token is required.")
    if not args.page:
        raise ConanException("Status Page ID is required.")
    if not args.incident:
        raise ConanException("Incident ID is required.")
    if not args.event:
        raise ConanException("Event type is required.")

    status = 'resolved' if args.event == 'incident' else 'completed'
    payload = {
        "incident": {
            "status": status,
            "impact_override": 'none',
            "components": {component: 'operational' for component in args.components},
            "component_ids": args.components,
        }
    }
    if args.message:
        payload["incident"]["body"] = args.message
    return Requester().patch(f"pages/{args.page}/incidents/{args.incident}", token, payload, verify=not args.ignore_ssl)
