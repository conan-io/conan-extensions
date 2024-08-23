# Generators

## Ament

> ⚠️ Warning: This generator is under development and should not be used for ROS2 builds in production.

This a generator created to produce ament files of packages to consume from a ROS2 and colcon build.

Reference: https://docs.ros.org/en/foxy/How-To-Guides/Ament-CMake-Documentation.html


```sh
$ conan install --requires=fmt/10.0.0 --generator Ament
...
======== Finalizing install (deploy, generators) ========
cli: Writing generators to /home/danimtb/ros2-examples/conan_consumer
cli: Generator 'Ament' calling 'generate()'
cli: CMakeDeps necessary find_package() and targets for your CMakeLists.txt
    find_package(box2d)
    find_package(Boost)
    target_link_libraries(... box2d::box2d boost::boost)
CMakeDeps generator file name: cmakedeps_macros.cmake
CMakeDeps generator file name: box2d-config-version.cmake
CMakeDeps generator file name: box2d-release-x86_64-data.cmake
CMakeDeps generator file name: box2d-Target-release.cmake
CMakeDeps generator file name: box2dTargets.cmake
CMakeDeps generator file name: box2d-config.cmake
CMakeDeps generator file name: BoostConfigVersion.cmake
CMakeDeps generator file name: Boost-release-x86_64-data.cmake
CMakeDeps generator file name: Boost-Target-release.cmake
CMakeDeps generator file name: BoostTargets.cmake
CMakeDeps generator file name: BoostConfig.cmake
CMakeDeps generator file name: ZLIBConfigVersion.cmake
CMakeDeps generator file name: ZLIB-release-x86_64-data.cmake
CMakeDeps generator file name: ZLIB-Target-release.cmake
CMakeDeps generator file name: ZLIBTargets.cmake
CMakeDeps generator file name: ZLIBConfig.cmake
CMakeDeps generator file name: module-ZLIB-release-x86_64-data.cmake
CMakeDeps generator file name: module-ZLIB-Target-release.cmake
CMakeDeps generator file name: module-ZLIBTargets.cmake
CMakeDeps generator file name: FindZLIB.cmake
CMakeDeps generator file name: BZip2ConfigVersion.cmake
CMakeDeps generator file name: BZip2-release-x86_64-data.cmake
CMakeDeps generator file name: BZip2-Target-release.cmake
CMakeDeps generator file name: BZip2Targets.cmake
CMakeDeps generator file name: BZip2Config.cmake
CMakeDeps generator file name: module-BZip2-release-x86_64-data.cmake
CMakeDeps generator file name: module-BZip2-Target-release.cmake
CMakeDeps generator file name: module-BZip2Targets.cmake
CMakeDeps generator file name: FindBZip2.cmake
...
```
