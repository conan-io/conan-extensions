```sh
conan install . -of=build --build=missing -pr:h=./android_arm64.profile -pr:b=default
../waf configure build
```