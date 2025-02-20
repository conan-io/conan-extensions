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

We will create a BuildInfo with build_name=<config>_build build_number=1

mypkg depending on liba, liba already in Artifactory, we are only building mypkg.

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

# Create liba

conan create liba -s build_type=Release -tf=""
conan create liba -s build_type=Debug -tf=""

# We upload to Artifactory, we will pick the information for the build info from there later

conan upload "liba*" -r=develop -c

conan remove "liba*" -c

# Release CI JOB

# build mypkg Release, will pick liba from Artifactory

conan create mypkg --format=json -s build_type=Release --build="mypkg*" -r=develop > create_release.json

conan upload "mypkg*" -r=develop -c

# create the Build Info for Release and set the properties to the Artifacts in Artifactory

conan art:build-info create create_release.json release_build 1 develop --server=myartifactory --with-dependencies > release_build.json

# Upload the Build Info

conan art:build-info upload release_build.json --server=myartifactory

# Debug CI JOB

# build mypkg Debug, will pick liba from Artifactory

conan create mypkg --format=json -s build_type=Debug --build="mypkg*" -r=develop > create_debug.json

conan upload "mypkg*" -r=develop -c

# create the Build Info for Debug and set the properties to the Artifacts in Artifactory

conan art:build-info create create_debug.json debug_build 1 develop --server=myartifactory --with-dependencies > debug_build.json

# Upload the Build Info

conan art:build-info upload debug_build.json --server=myartifactory

# parent CI job

conan art:build-info append aggregated_build 1 --server=myartifactory --build-info=release_build,1 --build-info=debug_build,1 > aggregated_build.json
conan art:build-info upload aggregated_build.json --server=myartifactory

# Still in Beta

conan art:build-info create-bundle aggregated_build.json develop aggregated_bundle 1.0 test_key_pair --server=myartifactory 
```
