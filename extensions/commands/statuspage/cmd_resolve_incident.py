import requests
from conan.cli.command import conan_command
from conan.api.conan_api import ConanAPI
from conan.api.output import ConanOutput
from conan.errors import ConanException
from statuspage_utils import get_token, output_json


__version__ = "0.1.0"


@conan_command(group="Status Page", formatters={"json": output_json})
def resolve_incident(conan_api: ConanAPI, parser, subparser, *args):
    """
    Resolve an existing incident in Status Page.

    https://developer.statuspage.io/#operation/patchPagesPageIdIncidentsIncidentId
    """
    parser.add_argument("-tk", "--token", type=str, help="Status Page API token")
    parser.add_argument("-ic", "--incident", type=str, help="Existing incident ID")
    parser.add_argument('-e', '--event', help="Event type to be finished", choices=["maintenance", "incident"])
    parser.add_argument("-p", "--page", type=str, help="Status Page ID")
    parser.add_argument('-c', "--components", help="Incident components", nargs="+")
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

    output = ConanOutput()
    status = 'resolved' if args.event == 'incident' else 'completed'
    url = f"https://api.statuspage.io/v1/pages/{args.page}/incidents/{args.incident}"
    payload = {
        "incident": {
            "status": status,
            "impact_override": 'none',
            "components": {component: 'operational' for component in args.components},
            "component_ids": args.components,
        }
    }
    output.info(f"Resolving the incident: {args.incident}")
    headers = {"Authorization": f"OAuth {token}", "Content-Type": "application/json"}
    response = requests.patch(url, json=payload, headers=headers, verify=not args.ignore_ssl)
    response.raise_for_status()
    output.info(f"Status Page API response ({response.status_code}):\n{response.json()}")
