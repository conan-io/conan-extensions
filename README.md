# Conan Extensions
This repository contains extensions for Conan, such as [custom commands](https://docs.conan.io/2/reference/extensions/custom_commands.html)
and [deployers](https://docs.conan.io/2/reference/extensions/deployers.html),
useful for different purposes, like artifactory tasks, conan-center-index, etc.

The contents of this repository are *not* production ready, they are intended as an aiding guide,
and you'll probably want to create your own custom commands and/or deployers taking these as a base to ensure they meet your needs.

### Conan config as installer

To install all the available extensions, run:

```
conan config install https://github.com/conan-io/conan-extensions.git
```

Afterwards, running `conan --help` should show you all the custom commands available.

### Custom Commands

These are the current supported custom commands:

#### [Convert txt](extensions/commands/migrate/)

Gets a `conanfile.txt` as input and outputs its equivalent `conanfile.py`

```
conan migrate:convert-txt conanfile.txt > conanfile.py
```

### Testing

To validate a new extension, it's possible to write a test which exercises its usage.
You can use [pytest](https://docs.pytest.org) with [tox](https://tox.wiki/en/latest/) for testing and manegable virtual environment, producing a stable environment.

```
TOXENV=conan-latest tox
```

### LICENSE

[MIT](LICENSE)
