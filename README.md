# Conan Extensions
This repository contains extensions for Conan, such as [custom commands](https://docs.conan.io/2/reference/extensions/custom_commands.html)
and [deployers](https://docs.conan.io/2/reference/extensions/deployers.html),
useful for different purposes, like [Artifactory](https://jfrog.com/artifactory) tasks, conan-center-index, etc.

The contents of this repository are *not* production ready, they are intended as an aiding guide,
and you'll probably want to create your own custom commands and/or deployers taking these as a base to ensure they meet your needs.

## Conan config install

To install all the available extensions, run:

```
conan config install https://github.com/conan-io/conan-extensions.git
```

Afterwards, running `conan --help` should show you all the custom commands available.

### Custom Commands

These are the currently supported custom commands:

#### [Convert txt](extensions/commands/migrate/)

Gets a `conanfile.txt` as input and outputs its equivalent `conanfile.py`

```
conan migrate:convert-txt conanfile.txt > conanfile.py
```


#### [List v2 ready](extensions/commands/cci/cmd_list_v2_ready.py)

For the conan-center-index recipe folder, it exports all the references found and checks if the recipe revision exists in the remote. If the `profile` flag is used, it will check that binaries exist in the remote as well.

> **Note:** This command is intended to work with the Conan hooks active.

**Parameters**
- **path** _Required_: Path to a folder containing the recipes to be checked.
- **remote** _Required_: Remote repository to check the recipes against it.

**Flags**
- **profile** _Optional_: Profile to check for binaries (can be more than one).
- **skip-binaries** _Optional_: Do not check if binary packages are available

```
$ conan cci:list-v2-ready conan-center-index/recipes conan-center --profile linux-gcc
{
    "fmt": {
        "9.1.0": {
            "exported": true,
            "latest_local_revision": "6708c9d84f98d56a6d9f2e6c2d5639ba",
            "is_latest_local_revision_in_remote": false,
            "binary_status_per_profile": {
                "linux-gcc": "Present"
            }
        },
        "9.0.0": {
            "exported": true,
            "latest_local_revision": "6708c9d84f98d56a6d9f2e6c2d5639ba",
            "is_latest_local_revision_in_remote": false,
            "binary_status_per_profile": {
                "linux-gcc": "Missing"
            }
        }
    }
}
```

### Testing

To validate a new extension, it's possible to write a test that exercises its usage.
You can use [pytest](https://docs.pytest.org) for testing, producing a stable environment.

```
pytest .
```

We recommend testing with Python 3.6 to respect the [minimum version required](https://github.com/conan-io/tribe/blob/main/design/003-codebase-python.md) for Conan 2.0

### LICENSE

[MIT](LICENSE)
