## Lipo deployers

These deployers create universal binaries on macOS or iOS.
They are similar to Conan's full_deploy deployer but run `lipo` to
produce universal binaries. An Xcode project can use the `full_deploy`
folder to compile a universal application.


#### [lipo](lipo.py)

This deployer is identical to `full_deploy` except single architecture universal
binaries will be created and a subfolder will not be created with the arch name.


#### [lipo_add](lipo_add.py)

This deployer doesn't remove the existing `full_deploy` folder but adds an architecture
to the existing universal binaries. It is an error to run this more than once for a given
architecture. Universal binaries can only contain one binary per architecture. See
`lipo -create` for more information.

```sh
$ conan install . --deployer=lipo -s arch=x86_64
$ conan install . --deployer=lipo_add -s arch=armv8
```

Profiles can be used to handle additional settings, for example when the architectures
have a different minimum deployment OS.


## Sample profiles

#### x86_64
```
[settings]
arch=x86_64
build_type=Release
compiler=apple-clang
compiler.cppstd=gnu17
compiler.libcxx=libc++
compiler.version=14
os=Macos
os.version=10.13
```

#### armv8
```
[settings]
arch=armv8
build_type=Release
compiler=apple-clang
compiler.cppstd=gnu17
compiler.libcxx=libc++
compiler.version=14
os=Macos
os.version=11.0
```
