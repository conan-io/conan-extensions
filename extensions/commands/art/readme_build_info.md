## [``conan art:build-info``](cmd_build_info.py)

```
$ conan art:build-info --help
usage: conan build-info [-h] [-v [V]] [-cc CORE_CONF] {append,create,create-bundle,delete,get,promote,upload} ...

Manages JFrog Build Info (https://www.buildinfo.org/)

positional arguments:
  {append,create,create-bundle,delete,get,promote,upload}
                        sub-command help
    append              Append published build to the build info.
    create              Creates BuildInfo from a Conan graph json from a conan install or create.
    create-bundle       Creates an Artifactory Release Bundle from the information of the Build Info
    delete              Removes builds stored in Artifactory. Useful for cleaning up old build info data.
    get                 Get Build Info information.
    promote             Promote the BuildInfo from the source to the target repository.
    upload              Uploads BuildInfo json to repository.

optional arguments:
  -h, --help            show this help message and exit
  -v [V]                Level of detail of the output. Valid options from less verbose to more verbose: -vquiet, -verror, -vwarning, -vnotice, -vstatus, -v or -vverbose, -vv or -vdebug,
                        -vvv or -vtrace
  -cc CORE_CONF, --core-conf CORE_CONF
                        Define core configuration, overwriting global.conf values. E.g.: -cc core:non_interactive=True
```

### ``conan art:build-info append``

```
$ conan art:build-info append --help
usage: conan build-info append [-h] [-v [V]] [-cc CORE_CONF] [--project PROJECT] [--server SERVER] [--url URL] [--user USER] [--password PASSWORD] [--token TOKEN]
                               [--build-info BUILD_INFO]
                               build_name build_number

Append published build to the build info.

positional arguments:
  build_name            The current build name.
  build_number          The current build number.

optional arguments:
  -h, --help            show this help message and exit
  -v [V]                Level of detail of the output. Valid options from less verbose to more verbose: -vquiet, -verror, -vwarning, -vnotice, -vstatus, -v or -vverbose, -vv or -vdebug,
                        -vvv or -vtrace
  -cc CORE_CONF, --core-conf CORE_CONF
                        Define core configuration, overwriting global.conf values. E.g.: -cc core:non_interactive=True
  --project PROJECT     Project key for the Build Info in Artifactory
  --server SERVER       Server name of the Artifactory to get the build info from.
  --url URL             Artifactory url, like: https://<address>/artifactory.
  --user USER           User name for the Artifactory server.
  --password PASSWORD   Password for the Artifactory server.
  --token TOKEN         Token for the Artifactory server.
  --build-info BUILD_INFO
                        Name and number for the Build Info already published in Artifactory. You can add multiple Builds like --build-info=build_name,build_number --build-
                        info=build_name,build_number
```

### ``conan art:build-info create``

```
$ usage: conan build-info create [-h] [-v [V]] [-cc CORE_CONF] [--server SERVER] [--url URL] [--user USER] [--password PASSWORD] [--token TOKEN] [--build-url BUILD_URL]
                               [--with-dependencies] [--add-cached-deps]
                               json build_name build_number repository

Creates BuildInfo from a Conan graph json from a conan install or create.

positional arguments:
  json                  Conan generated JSON output file.
  build_name            Build name property for BuildInfo.
  build_number          Build number property for BuildInfo.
  repository            Artifactory repository name where artifacts are located -not the conan remote name-.

optional arguments:
  -h, --help            show this help message and exit
  -v [V]                Level of detail of the output. Valid options from less verbose to more verbose: -vquiet, -verror, -vwarning, -vnotice, -vstatus, -v or -vverbose, -vv or -vdebug,
                        -vvv or -vtrace
  -cc CORE_CONF, --core-conf CORE_CONF
                        Define core configuration, overwriting global.conf values. E.g.: -cc core:non_interactive=True
  --server SERVER       Server name of the Artifactory to get the build info from.
  --url URL             Artifactory url, like: https://<address>/artifactory. This may be not necessary if all the information for the Conan artifacts is present in the local cache.
  --user USER           User name for the Artifactory server.
  --password PASSWORD   Password for the Artifactory server.
  --token TOKEN         Token for the Artifactory server.
  --build-url BUILD_URL
                        Build url property for BuildInfo.
  --with-dependencies   Whether to add dependencies information or not. Default: false.
  --add-cached-deps     It will add not only the Conan packages that are built but also the ones that are used from the cache but not built. Default: false.
```

### ``conan art:build-info create-bundle``

```
$ conan art:build-info create-bundle --help
usage: conan build-info create-bundle [-h] [-v [V]] [-cc CORE_CONF] [--server SERVER] [--url URL] [--user USER] [--password PASSWORD] [--token TOKEN]
                                      json repository bundle_name bundle_version sign_key_name

Creates an Artifactory Release Bundle from the information of the Build Info

positional arguments:
  json                  BuildInfo JSON.
  repository            Artifactory repository where artifacts are located.
  bundle_name           The created bundle name.
  bundle_version        The created bundle version.
  sign_key_name         Signing Key name.

optional arguments:
  -h, --help            show this help message and exit
  -v [V]                Level of detail of the output. Valid options from less verbose to more verbose: -vquiet, -verror, -vwarning, -vnotice, -vstatus, -v or -vverbose, -vv or -vdebug,
                        -vvv or -vtrace
  -cc CORE_CONF, --core-conf CORE_CONF
                        Define core configuration, overwriting global.conf values. E.g.: -cc core:non_interactive=True
  --server SERVER       Server name of the Artifactory to get the build info from.
  --url URL             Artifactory url, like: https://<address>/artifactory.
  --user USER           User name for the Artifactory server.
  --password PASSWORD   Password for the Artifactory server.
  --token TOKEN         Token for the Artifactory server.
```

### ``conan art:build-info delete``

```
$ conan art:build-info delete --help
usage: conan build-info delete [-h] [-v [V]] [-cc CORE_CONF] [--project PROJECT] [--server SERVER] [--url URL] [--user USER] [--password PASSWORD] [--token TOKEN]
                               [--build-number BUILD_NUMBER] [--delete-artifacts] [--delete-all]
                               build_name

Removes builds stored in Artifactory. Useful for cleaning up old build info data.

positional arguments:
  build_name            BuildInfo name to delete.

optional arguments:
  -h, --help            show this help message and exit
  -v [V]                Level of detail of the output. Valid options from less verbose to more verbose: -vquiet, -verror, -vwarning, -vnotice, -vstatus, -v or -vverbose, -vv or -vdebug,
                        -vvv or -vtrace
  -cc CORE_CONF, --core-conf CORE_CONF
                        Define core configuration, overwriting global.conf values. E.g.: -cc core:non_interactive=True
  --project PROJECT     Project key for the Build Info in Artifactory
  --server SERVER       Server name of the Artifactory to get the build info from.
  --url URL             Artifactory url, like: https://<address>/artifactory.
  --user USER           User name for the Artifactory server.
  --password PASSWORD   Password for the Artifactory server.
  --token TOKEN         Token for the Artifactory server.
  --build-number BUILD_NUMBER
                        BuildInfo numbers to promote. You can add several build-numbers for the same build-name, like: --build-number=1 --build-number=2.
  --delete-artifacts    Build artifacts are also removed provided they have the corresponding build.name and build.number properties attached to them. Default false.
  --delete-all          The whole build is removed. Default false.
```

### ``conan art:build-info get``

```
$ conan art:build-info get --help
usage: conan build-info get [-h] [-v [V]] [-cc CORE_CONF] [--project PROJECT] [--server SERVER] [--url URL] [--user USER] [--password PASSWORD] [--token TOKEN] build_name build_number

Get Build Info information.

positional arguments:
  build_name            BuildInfo name to get.
  build_number          BuildInfo number to get.

optional arguments:
  -h, --help            show this help message and exit
  -v [V]                Level of detail of the output. Valid options from less verbose to more verbose: -vquiet, -verror, -vwarning, -vnotice, -vstatus, -v or -vverbose, -vv or -vdebug,
                        -vvv or -vtrace
  -cc CORE_CONF, --core-conf CORE_CONF
                        Define core configuration, overwriting global.conf values. E.g.: -cc core:non_interactive=True
  --project PROJECT     Project key for the Build Info in Artifactory
  --server SERVER       Server name of the Artifactory to get the build info from.
  --url URL             Artifactory url, like: https://<address>/artifactory.
  --user USER           User name for the Artifactory server.
  --password PASSWORD   Password for the Artifactory server.
  --token TOKEN         Token for the Artifactory server.
```

### ``conan art:build-info promote``

```
$ cconan art:build-info promote --help
usage: conan build-info promote [-h] [-v [V]] [-cc CORE_CONF] [--project PROJECT] [--server SERVER] [--url URL] [--user USER] [--password PASSWORD] [--token TOKEN] [--dependencies]
                                [--comment COMMENT]
                                build_name build_number source_repo target_repo

Promote the BuildInfo from the source to the target repository.

positional arguments:
  build_name            BuildInfo name to promote.
  build_number          BuildInfo number to promote.
  source_repo           Artifactory repository to get artifacts from.
  target_repo           Artifactory repository to promote artifacts to.

optional arguments:
  -h, --help            show this help message and exit
  -v [V]                Level of detail of the output. Valid options from less verbose to more verbose: -vquiet, -verror, -vwarning, -vnotice, -vstatus, -v or -vverbose, -vv or -vdebug,
                        -vvv or -vtrace
  -cc CORE_CONF, --core-conf CORE_CONF
                        Define core configuration, overwriting global.conf values. E.g.: -cc core:non_interactive=True
  --project PROJECT     Project key for the Build Info in Artifactory
  --server SERVER       Server name of the Artifactory to get the build info from.
  --url URL             Artifactory url, like: https://<address>/artifactory.
  --user USER           User name for the Artifactory server.
  --password PASSWORD   Password for the Artifactory server.
  --token TOKEN         Token for the Artifactory server.
  --dependencies        Whether to copy the build's dependencies or not. Default: false.
  --comment COMMENT     An optional comment describing the reason for promotion. Default: ''
```

### ``conan art:build-info upload``

```
$ conan art:build-info upload --help
usage: conan build-info upload [-h] [-v [V]] [-cc CORE_CONF] [--project PROJECT] [--server SERVER] [--url URL] [--user USER] [--password PASSWORD] [--token TOKEN] build_info

Uploads BuildInfo json to repository.

positional arguments:
  build_info            BuildInfo json file.

optional arguments:
  -h, --help            show this help message and exit
  -v [V]                Level of detail of the output. Valid options from less verbose to more verbose: -vquiet, -verror, -vwarning, -vnotice, -vstatus, -v or -vverbose, -vv or -vdebug,
                        -vvv or -vtrace
  -cc CORE_CONF, --core-conf CORE_CONF
                        Define core configuration, overwriting global.conf values. E.g.: -cc core:non_interactive=True
  --project PROJECT     Project key for the Build Info in Artifactory
  --server SERVER       Server name of the Artifactory to get the build info from.
  --url URL             Artifactory url, like: https://<address>/artifactory.
  --user USER           User name for the Artifactory server.
  --password PASSWORD   Password for the Artifactory server.
  --token TOKEN         Token for the Artifactory server.
```