## Conan Center Index specific commands
These are commands that are specific to the structure used in Conan Center Index, and can be useful for forks of it too.


#### [List v2 ready](cmd_list_v2_ready.py)

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


# [Export all versions](cmd_export_all_versions.py)

Exports all the references passed to it. This command assumes that it's ran in the conan-center-index root folder.

If **list** or **name** is not defined, **path** will be used.
This expects all recipe folders to contain a `config.yml` file.

**Parameters**
- **path** _Choice_: Path to a folder containing the recipes to be checked.
- **list** _Choice_: YAML list including the recipes to export. Should have a single `recipes` key containing the list.
- **name** _Choice_: Name of recipe to export.


```
$ tree .
.
└── recipes
    ├── span-lite
    │         ├── all
    │         │         ├── conandata.yml
    │         │         ├── conanfile.py
    │         │         ├── test_package
    │         │         │         ├── CMakeLists.txt
    │         │         │         ├── conanfile.py
    │         │         │         └── test_package.cpp
    │         │         └── test_v1_package
    │         │             ├── CMakeLists.txt
    │         │             └── conanfile.py
    │         └── config.yml
    └── zlib
        ├── all
        │         ├── conandata.yml
        │         ├── conanfile.py
        │         ├── patches
        │         │         ├── 1.2.13
        │         │         │         └── 0001-Fix-cmake.patch
        │         │         └── 1.2.x
        │         │             ├── 0001-fix-cmake.patch
        │         │             ├── 0002-gzguts-xcode12-compile-fix.patch
        │         │             ├── 0003-gzguts-fix-widechar-condition.patch
        │         │             ├── 0004-Fix-a-bug-when-getting-a-gzip-header-extra-field-wit.patch
        │         │             └── 0005-Fix-extra-field-processing-bug-that-dereferences-NUL.patch
        │         ├── test_package
        │         │         ├── CMakeLists.txt
        │         │         ├── CMakeUserPresets.json
        │         │         ├── conanfile.py
        │         │         └── test_package.c
        │         └── test_v1_package
        │             ├── CMakeLists.txt
        │             └── conanfile.py
        └── config.yml
```

And then:

```
$ conan cci:export-all-versions --path conan-center-index/recipes/

...
EXPORTED RECIPES
zlib: exported 3 versions
span-lite: exported 9 versions
FAILED TO EXPORT
RECIPE REFERENCES
zlib/1.2.13#416618fa04d433c6bd94279ed2e93638
zlib/1.2.12#0de8ff7f99079cd07341311c9ead89a2
zlib/1.2.11#46d152db0d590d20e500f73a7e727f14
span-lite/0.6.0#5bfea5cdd772dd1236ce982842b040f1
span-lite/0.7.0#5bfea5cdd772dd1236ce982842b040f1
span-lite/0.8.0#5bfea5cdd772dd1236ce982842b040f1
span-lite/0.8.1#5bfea5cdd772dd1236ce982842b040f1
span-lite/0.9.0#5bfea5cdd772dd1236ce982842b040f1
span-lite/0.9.2#5bfea5cdd772dd1236ce982842b040f1
span-lite/0.10.0#5bfea5cdd772dd1236ce982842b040f1
span-lite/0.10.1#5bfea5cdd772dd1236ce982842b040f1
span-lite/0.10.3#5bfea5cdd772dd1236ce982842b040f1
VERSION LIST
['zlib/1.2.13', 'zlib/1.2.12', 'zlib/1.2.11', 'span-lite/0.6.0', 'span-lite/0.7.0', 'span-lite/0.8.0', 'span-lite/0.8.1', 'span-lite/0.9.0', 'span-lite/0.9.2', 'span-lite/0.10.0', 'span-lite/0.10.1', 'span-lite/0.10.3']
```

# [Upgrade Qt recipe version](cmd_upgrade_qt_recipe.py)

Upgrades the Qt recipe with a new version of Qt. This command assumes that it's ran in the folder containing qt's `config.yml` file (in conan-center-index: recipes/qt)

This command does the following:

- add the version to `config.yml`
- add the sources to  `conandata.yml`
- reuse the patches from the previous version in `conandata.yml`
- create `qtmodulesX.y.z.conf`
- add the eventual new modules in `conanfile.py`'s `_submodules` variable. This can be done automatically only if the conanfile.py is already compatible with conan V2.

**Parameters**

- **version** _Required_: Version to add to Qt recipe.

```bash
$ conan cci:upgrade-qt-recipe 6.4.3
qt version 6.4.3 successfully added to 6.x.x.
```
