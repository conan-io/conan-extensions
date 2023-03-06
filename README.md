# Conan Extensions
This repository contains extensions for Conan, such as [custom commands](https://docs.conan.io/2/reference/extensions/custom_commands.html)
and [deployers](https://docs.conan.io/2/reference/extensions/deployers.html),
useful for different purposes, like [Artifactory](https://jfrog.com/artifactory) tasks, conan-center-index, etc.

The contents of this repository are *not* production ready, they are intended as an aiding guide,
and you'll probably want to create your own custom commands and/or deployers taking these as a base to ensure they meet your needs.

### Conan config install

To install all the available extensions, run:

```
conan config install https://github.com/conan-io/conan-extensions.git
```

Afterwards, running `conan --help` should show you all the custom commands available.

### Custom Commands

These are the currently supported custom commands:

#### [Clean](extensions/commands/management/cmd_clean.py)

Deletes (from the local cache or remotes) every recipe and package revision,
except for the latest package revision from the latest recipe revision.

#### [Convert txt](extensions/commands/migrate/)

Gets a `conanfile.txt` as input and outputs its equivalent `conanfile.py`

```
conan migrate:convert-txt conanfile.txt > conanfile.py
```


### Deployers

#### [Deploy sources](extensions/deployers/sources_deploy.py)

Copies the sources of every dependency of the recipe into its output folder

#### [Deploy licenses](extensions/deployers/licenses_deploy.py)

Copies all the licenses of every dependency of the recipe into its output folder

### Testing

To validate a new extension, it's possible to write a test that exercises its usage.
You can use [pytest](https://docs.pytest.org) for testing, producing a stable environment.

```
pytest .
```

We recommend testing with Python 3.6 to respect the [minimum version required](https://github.com/conan-io/tribe/blob/main/design/003-codebase-python.md) for Conan 2.0

### LICENSE

[MIT](LICENSE)
