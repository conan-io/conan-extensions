## Migration commands
These are commands intended to ease in migrations, both from old Conan versions and between different aspects of it.


#### [Convert txt](cmd_convert_txt.py)

Gets the path to a `conanfile.txt` as input and outputs its equivalent `conanfile.py` to the standard output


**Parameters**
- **path** _Required_: Path to a conanfile.txt

```
$ cat conanfile.txt

[requires]
zlib/1.2.13
fmt/9.1.0

[options]
fmt/*:header_only=True

```

```
$ conan migrate:convert-txt conanfile.txt

from conan import ConanFile

class Pkg(ConanFile):

    default_options = {'fmt/*:header_only': 'True'}

    def requirements(self):
        self.requires("zlib/1.2.13")
        self.requires("fmt/9.1.0")

    def build_requirements(self):
        pass

```