import json
import platform
import subprocess
import getpass


def get_token(args):
    """
    Get Status Page token from keychain or from command line argument.
    """
    token = args.token
    if not args.token and platform.system() == "Darwin":
        # INFO: https://scriptingosx.com/2021/04/get-password-from-keychain-in-shell-scripts/
        # security add-generic-password -s 'CLI Test'  -a 'armin' -w 'password123'
        # security find-generic-password -w -s 'CLI Test' -a 'armin'
        user = args.user or getpass.getuser()
        print(f"Getting Status Page token from keychain for user '{user}'")
        output = subprocess.run(["security", "find-generic-password", "-a", user, "-s", args.service, "-w"], capture_output=True, text=True)
        token = output.stdout.strip()
    return token


def output_json(results: dict):
    """
    Print results in JSON format.
    """
    print(json.dumps(results, indent=2))
