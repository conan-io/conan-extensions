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
* supports all arguments used by `conan install`, see `conan install-universal --help`

This is implemented with the following steps:

1. Calculate the universal packages to build, as with `conan graph build-order`
2. Build these references for each architecture (ignoring the -b argument and building any
   required dependencies).
3. Restart the install with the universal profile and -b 'never'. The recipes are replaced with
   code to run lipo on the single architecture packages.

Note: this command builds for each architecture with and some arguments
may break something. This command may load the local cache with
both universal and single architecture binaries if they need to be built.

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
