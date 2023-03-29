## Conan Center Index specific commands
These are commands that are specific to the structure used in Conan Center Index, and can be useful for forks of it too.


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