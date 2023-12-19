import requests
from conan.cli.command import conan_command
from conan.api.conan_api import ConanAPI
from conan.api.output import cli_out_write
from conan.errors import ConanException
from statuspage_utils import get_token, output_json
from datetime import datetime, timezone, timedelta


__version__ = "0.1.0"


def output_text(results: dict):
    lines = [f"Maintenance ID: {results['id']}", f"Created at: {results['created_at']}", f"Name: {results['name']}",
             f"Scheduled for (UTC) {results['scheduled_for']}",
             f"Status: {results['status']}", f"Impact: {results['impact']}", f"URL: {results['shortlink']}"]
    cli_out_write("Scheduled maintenance:\n{}\n".format('\n'.join(lines)))


@conan_command(group="Status Page", formatters={"json": output_json, "text": output_text})
def schedule_maintenance(conan_api: ConanAPI, parser, *args) -> dict:
    """
    Schedule a new maintenance window in Status Page.

    https://developer.statuspage.io/#operation/postPagesPageIdIncidents
    """
    parser.add_argument("-tk", "--token", type=str, help="Status Page API token")
    parser.add_argument("-t", "--title", type=str, help="Incident title")
    parser.add_argument("-m", "--message", type=str, help="Incident body description")
    parser.add_argument("-p", "--page", type=str, help="Status Page ID")
    parser.add_argument('-c', "--components", help="Incident components", nargs="+")
    parser.add_argument('-s', '--scheduled', type=str, help="Scheduled time (UTC) in ISO 8601 format (YYYY-MM-DDTHH:MM:SS.sssZ)", default='now')
    parser.add_argument('-g', '--ignore-ssl', action='store_true', help="Ignore SSL verification")
    parser.add_argument('-ku', '--keychain-user', type=str, help="Status Page username")
    parser.add_argument("-ks", "--keychain-service", type=str, help="Keychain service", default="statuspage-token")
    args = parser.parse_args(*args)

    token = get_token(args)
    if not token:
        raise ConanException("Status Page API token is required.")
    if not args.page:
        raise ConanException("Status Page ID is required.")
    if not args.title:
        raise ConanException("Incident title is required.")

    url = f"https://api.statuspage.io/v1/pages/{args.page}/incidents"
    # scheduled_for
    sched = args.scheduled or 'now'
    if sched == 'now':
        current_time_utc = datetime.now(timezone.utc)
        new_time_utc = current_time_utc + timedelta(minutes=1)
        sched = new_time_utc.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
    # scheduled_until
    sched_until = datetime.strptime(sched, "%Y-%m-%dT%H:%M:%S.%fZ") + timedelta(hours=8)
    sched_until = sched_until.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
    payload = {
        "incident": {
            "name": args.title,
            "impact_override": 'maintenance',
            "status": 'scheduled',
            "scheduled_for": sched,
            "scheduled_until": sched_until,
            "scheduled_remind_prior": True,
            "auto_transition_to_maintenance_state": True,
            "auto_transition_to_operational_state": True,
            "scheduled_auto_in_progress": True,
            "scheduled_auto_completed": False,
            "auto_transition_deliver_notifications_at_start": False,
            "auto_transition_deliver_notifications_at_end": True,
            "deliver_notifications": True,
            "body": args.message,
            "components": {component: 'under_maintenance' for component in args.components},
            "component_ids": args.components,
        }
    }
    headers = {"Authorization": f"OAuth {token}", "Content-Type": "application/json"}
    response = requests.post(url, json=payload, headers=headers, verify=not args.ignore_ssl)
    response.raise_for_status()
    return response.json()
