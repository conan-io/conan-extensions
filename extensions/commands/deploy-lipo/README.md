## Lipo commands

These are commands to deploy macOS or iOS universal binaries.
This wraps around Conan's full_deploy deployer and then runs `lipo` to
produce universal binaries.


#### [Deploy lipo](cmd_deploy_lipo.py)


**Parameters**

The same parameters as `deploy` except multiple profiles should be specified.

```
$ conan deploy-lipo . -pr x8_64 -pr armv8 -b missing -r conancenter
```

This assumes profiles named x86_64 and armv8 with corresponding architectures.
Universal binaries can only have one binary per architecture but each can have
different settings, e.g. minimum deployment OS:

## x86_64
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

## armv8
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


#### [Example project](xcode)


```
cd ./xcode
conan deploy-lipo . -pr x86_64 -pr armv8 -b missing
conan build .
```

Verify the architectures:
```
file ./build/Release/example
```
