## [Install macOS/iOS universal binaries](cmd_install_universal.py)

Install dependent packages as universal binaries packages.
Conan v2 introduces support for multiple architectures, e.g. -s arch=armv8|x86_64
however this is largely limited to CMake.

For CMake-based project that only depends on other CMake-based recipes, it's now
possible to run:

```
conan install . -pr:h universal -pr:b default -b missing
conan build . -pr:h universal -pr:b default
```

However, many other recipes use autotools or other build systems that don't support
universal binaries. This command skips the usual build() / package() steps and
runs lipo when a universal package is needed.

**This command is in an experimental stage, feedback is welcome.**

**Parameters**
* supports all arguments used by `conan install`, see `conan install_universal --help`

Note: many arguments are not correctly passed to the single architecture installs.
Currently this includes -o and -s settings. The Conan dependency graph does not support
building multiple architectures so this executes Conan again in a new process.

**Profile**
The multi-architecture must be specified in the host profile.
The build profile will likely be a single architecture, although the default
binary compatibility plugin does not know that universal binaries can be used
for single architecture profiles.

```
[settings]
arch=armv8|x86_64
build_type=Release
compiler=apple-clang
compiler.cppstd=17
compiler.libcxx=libc++
compiler.version=15
os=Macos
os.version=11.0
```

Also make sure to use += not = if you define CXXFLAGS or you will override the -arch flag
to autotools.

```
[buildenv]
CFLAGS+=-fvisibility=hidden
CXXFLAGS+=-fvisibility=hidden -fvisibility-inlines-hidden
```

Usage:
```
conan install-universal . -pr:h universal -pr:b default -b missing
conan build . -pr:h universal -pr:b default
```
