Using Build Info with Conan
===========================

Demo Pre-Requisites
-------------------

Have an Artifactory instance running (needs a version with API support, Artifactory
Community Edition won't work for this) with at least one repository called ``develop``.

To test the Relase Bundles generation you also need a [signing key already
created](https://jfrog.com/help/r/jfrog-artifactory-documentation/setting-up-rsa-keys-pairs)
in Artifactory.

To easily run an Artifactory in Docker:

```
docker run --name artifactory -d -e JF_SHARED_DATABASE_TYPE=derby -e JF_SHARED_DATABASE_ALLOWNONPOSTGRESQL=true -p 8081:8081 -p 8082:8082 releases-docker.jfrog.io/jfrog/artifactory-pro:latest
```

To test, you need to have the extensions installed:

```
conan config install https://github.com/conan-io/conan-extensions.git
```

We will create a BuildInfo with ``build_name=<Release/Debug>_build`` ``build_number=1``
and then create an aggregated Build Info for both Release and Debug configurations

``mypkg`` depending on ``liba``.

Two paralell jobs creating Release and Debug, each one with a BuildInfo, then aggregate
them

![Alt build](diagram.png?raw=true)

Running the demo
----------------

```

# Add the repos if you haven't already

conan remote add develop http://localhost:8081/artifactory/api/conan/develop
conan remote login develop admin -p password

# Also configure the server for the Build Info command

conan art:server add myartifactory http://localhost:8081/artifactory --user=admin --password=password

# Also you need to have the packages ready for creation:

conan new cmake_lib -d name=liba -d version=1.0 -o=liba 
conan new cmake_lib -d name=mypkg -d version=1.0 -o=mypkg -d requires="liba/1.0"

# Start from a clean state

conan remove "*" -r=develop -c
conan remove "liba*" -c
conan remove "mypkg*" -c

# We create liba before building mypkg

conan create liba -s build_type=Release -tf=""
conan create liba -s build_type=Debug -tf=""
conan upload "liba*" -r=develop -c

# Release CI JOB

# build mypkg Release

conan create mypkg --format=json -s build_type=Release --build="mypkg*" -r=develop -tf="" > create_release.json
conan upload "mypkg*" -r=develop -c

# create the Build Info for Release and set the properties to the Artifacts in Artifactory

conan art:build-info create create_release.json release_build 1 develop --server=myartifactory --with-dependencies > release_build.json

# Upload the Build Info

conan art:build-info upload release_build.json --server=myartifactory

# Debug CI JOB

# build mypkg Debug, will pick liba from Artifactory

conan create mypkg --format=json -s build_type=Debug --build="mypkg*" -r=develop -tf="" > create_debug.json

conan upload "mypkg*" -r=develop -c

# create the Build Info for Debug and set the properties to the Artifacts in Artifactory

conan art:build-info create create_debug.json debug_build 1 develop --server=myartifactory --with-dependencies > debug_build.json

# If you are using packages from different repositories, you can specify the repositories in order.
# Conan will associate each artifact with the first repository in which it is found.
# conan art:build-info create create_release.json release_build 1 develop third-party --server=myartifactory --with-dependencies > release_build.json

# Upload the Build Info

conan art:build-info upload debug_build.json --server=myartifactory

# Bundles aggregating both Release and Debug Builds

conan art:build-info bundle-create aggregated_bundle 1.0 test_key_pair --server=myartifactory --build-info=debug_build,1 --build-info=release_build,1

# You can delete the bundle 
conan art:build-info bundle-delete aggregated_bundle 1.0 --server=myartifactory
```
