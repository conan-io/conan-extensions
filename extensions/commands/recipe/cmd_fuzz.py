from conan.api.conan_api import ConanAPI
from conan.cli.args import add_reference_args
from conan.cli.command import conan_command

import random


@conan_command()
def fuzz(conan_api: ConanAPI, parser, *args):
    """
    command to fuzz a recipe
    """
    parser.add_argument("recipe", help="Path to the recipe to fuzz")
    add_reference_args(parser)
    parser.add_argument("-io", "--ignore-option", action="append", default=[], help="Options to ignore")
    parser.add_argument("-n", default=5, help="Number of iterations to fuzz")
    args = parser.parse_args(*args)

    inspection = conan_api.command.run(f"inspect {args.recipe} --format=json")

    results = []

    for x in range(int(args.n)):
        options = {}
        for option, values in inspection["options_definitions"].items():
            if option in args.ignore_option:
                continue
            if values:
                value = random.choice(values)
                options[option] = value

        name = ""
        if args.name:
            name = f"--name {args.name}"
        version = ""
        if args.version:
            version = f"--version {args.version}"
        user = ""
        if args.user:
            user = f"--user {args.user}"
        channel = ""
        if args.channel:
            channel = f"--channel {args.channel}"
        cli_options = " ".join([f'-o {k}={v}' for k, v in options.items()])
        try:
            conan_api.command.run(f"create {args.recipe} -r conancenter {name} {version} {user} {channel} {cli_options} --build missing --format=json")
            results.append((options, True))
        except:
            results.append((options, False))

    print(results)

