This is a more advanced cross compilation sample that allows targeting multiple
android ABIs at the same time. This is accomplished by creating separate
commands for each of the 4 ABIs (arm32, arm64, x86, x86_64)

## Building

Example for `arm32_debug`:

```sh
#install ('-of' must be build/<variant>)
conan install . -of=build/arm32_debug -pr:h=android_ndk.profile -pr:h=variants/arm32_debug.profile -pr:b=default --build=missing

#configure arm32 debug
waf configure_arm32_debug

#build
waf build_arm32_debug
```

Alternatively, you can also have waf invoke `conan install` for you during
configuration:

```sh
#configure arm32 debug
waf configure_arm32_debug --conan-install

#build
waf build_arm32_debug
```

### Available variants:

The following variants are available for this demo:

* `arm32_debug`
* `arm32_release`
* `arm64_debug`
* `arm64_release`
* `x86_debug`
* `x86_release`
* `x86_64_debug`
* `x86_64_release`

To run it, append the variant to the command, such as `configure_x86_debug`,
`clean_x86_debug`, etc. The available commands are:

* `configure`
* `build`
* `clean`
* `install` (warning: this will try to install to your system by default, pass
  `--prefix` to configure to change where they're installed)
* `uninstall`

Each command corresponds to a partial Conan profile in the `variants` folder,
which is combined with the base profile `android_ndk.profile` to compose the
final profile used for each target.