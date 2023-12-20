import json
import platform
import subprocess
import getpass


def get_token(args):
    """
    Get Status Page token from keychain or from command line argument.
    """
    token = args.token
    user = args.user or getpass.getuser()
    if not args.token and platform.system() == "Darwin":
        # INFO: https://scriptingosx.com/2021/04/get-password-from-keychain-in-shell-scripts/
        # security add-generic-password -s 'CLI Test'  -a 'armin' -w 'password123'
        # security find-generic-password -w -s 'CLI Test' -a 'armin'
        output = subprocess.run(["security", "find-generic-password", "-a", user, "-s", args.service, "-w"], capture_output=True, text=True)
        if output.returncode == 0:
            token = output.stdout.strip()
    elif not args.token and platform.system() == "Linux":
        # https://manpages.ubuntu.com/manpages/focal/man1/secret-tool.1.html
        output = subprocess.run(["secret-tool", "lookup", user, args.service], capture_output=True, text=True)
        if output.returncode == 0:
            token = output.stdout.strip()
    elif not args.token and platform.system() == "Windows":
        # TODO: https://learn.microsoft.com/en-us/powershell/scripting/learn/deep-dives/add-credentials-to-powershell-functions?view=powershell-7.4
        pass
    if not token:
        # https://github.com/jaraco/keyring
        try:
            import keyring
            token = keyring.get_password(args.service, args.user)
        except:
            pass
    return token


def output_json(results: dict):
    """
    Print results in JSON format.
    """
    print(json.dumps(results, indent=2))
