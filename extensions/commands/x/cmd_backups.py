import os
import shutil
import json

from conan.api.output import ConanOutput
from conan.cli.command import conan_command
from conan.errors import ConanException
from conans.util.dates import timestamp_now
from conans.util.sha import sha256


@conan_command(group="Backup sources handling")
def backups(conan_api, parser, *args):
    """
    This command will upload the backup sources of a package to the server.
    """
    parser.add_argument("reference", help="Reference of the package to backup")
    parser.add_argument("path", help="Path to source files for this reference")
    parser.add_argument("--url", help="Original URL of the file", default=None)
    args = parser.parse_args(*args)

    if not os.path.isfile(args.path):
        raise ConanException(f"File not found: {args.path}")

    with open(args.path, "rb") as f:
        checksum = sha256(f.read())

    ConanOutput().info(f"Calculated checksum: {checksum}")
    new_path = os.path.join(os.path.dirname(args.path), checksum)
    json_path = new_path + ".json"
    shutil.move(args.path, new_path)
    try:
        with open(json_path, "w") as f:
            json.dump({"references": {args.reference: [args.url] if args.url else []},
                       "timestamp": timestamp_now()}, f)

        conan_api.upload.upload_backup_sources([new_path, json_path])
    finally:
        shutil.move(new_path, args.path)
        if os.path.isfile(json_path):
            os.remove(json_path)