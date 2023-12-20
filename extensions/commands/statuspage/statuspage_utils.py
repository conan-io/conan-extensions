import json
import platform
import subprocess
import getpass
import argparse


def get_token(args):
    """
    Get Status Page token from keychain or from command line argument.
    """
    token = args.token
    user = args.keychain_user or getpass.getuser()
    if not token and platform.system() == "Darwin":
        # INFO: https://scriptingosx.com/2021/04/get-password-from-keychain-in-shell-scripts/
        # security add-generic-password -s 'CLI Test'  -a 'armin' -w 'password123'
        # security find-generic-password -w -s 'CLI Test' -a 'armin'
        output = subprocess.run(["security", "find-generic-password", "-a", user, "-s", args.service, "-w"], capture_output=True, text=True)
        if output.returncode == 0:
            token = output.stdout.strip()
    elif not token and platform.system() == "Linux":
        # https://manpages.ubuntu.com/manpages/focal/man1/secret-tool.1.html
        output = subprocess.run(["secret-tool", "lookup", user, args.service], capture_output=True, text=True)
        if output.returncode == 0:
            token = output.stdout.strip()
    elif not    token and platform.system() == "Windows":
        # TODO: https://learn.microsoft.com/en-us/powershell/scripting/learn/deep-dives/add-credentials-to-powershell-functions?view=powershell-7.4
        pass
    if not token:
        # https://github.com/jaraco/keyring
        try:
            import keyring
            token = keyring.get_password(args.service, user)
        except:
            pass
    return token


def add_common_arguments(parser: argparse.ArgumentParser) -> argparse.ArgumentParser:
    """
    Add common arguments to the parser.
    """
    parser.add_argument("-tk", "--token", type=str, help="Status Page API token")
    parser.add_argument("-p", "--page", type=str, help="Status Page ID")
    parser.add_argument('-g', '--ignore-ssl', action='store_true', help="Ignore SSL verification")
    parser.add_argument('-ku', '--keychain-user', type=str, help="Status Page username")
    parser.add_argument("-ks", "--keychain-service", type=str, help="Keychain service", default="statuspage-token")
    return parser


def output_json(results: dict):
    """
    Print results in JSON format.
    """
    print(json.dumps(results, indent=2))
