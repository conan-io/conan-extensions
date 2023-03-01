# conan-extensions
This repository contains extensions for Conan, such as custom commands and deployers,
useful for different purposes, like artifactory tasks, conan-center-index, etc.

The contents of this repository are *not* production ready, they are intended as an aiding guide,
and you'll probably want to create your own custom commands and/or deployers taking these as a base to ensure they meet your needs.

To install all the available extensions, run `conan config install https://github.com/conan-io/conan-extensions.git`.

Afterwards, running `conan --help` should show you all the custom commands available.

The current commands are:
 - `migrate:convert-txt`: Gets a `conanfile.txt` as input and returns its equivalent `conanfile.py`
