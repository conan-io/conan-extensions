## [``conan art:build-info``](cmd_build_info.py)

```
$ conan art:build-info --help
usage: conan build-info [-h] [-v [V]] [-cc CORE_CONF] [--out-file OUT_FILE] {append,bundle-create,bundle-delete,create,delete,get,promote,upload} ...

Manages JFrog Build Info (https://www.buildinfo.org/)

positional arguments:
  {append,bundle-create,bundle-delete,create,delete,get,promote,upload}
                        sub-command help
    append              Append published build to the build info.
    bundle-create       Creates an Artifactory Release Bundle (v2) from the information of the Build Info.
    bundle-delete       Deletes a Release Bundle v2 version and all its promotions. Both the Release Bundle attestation and all artifacts are removed.
    create              Creates BuildInfo from a Conan graph json. Refer to Conan documentation for commands that can output in that format.
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
  --out-file OUT_FILE   Write the output of the command to the specified file instead of stdout.
```

### ``conan art:build-info append``

```
$ conan art:build-info append --help
usage: conan art:build-info append [-h] [--out-file OUT_FILE] [-v [{quiet,error,warning,notice,status,verbose,debug,v,trace,vv}]] [-cc CORE_CONF] [--project PROJECT] [--server SERVER] [--url URL] [--user USER] [--password PASSWORD]
                                   [--token TOKEN] [--build-info BUILD_INFO] [--build-info-file BUILD_INFO_FILE]
                                   build_name build_number

Append published build to the build info.

positional arguments:
  build_name            The current build name.
  build_number          The current build number.

options:
  -h, --help            show this help message and exit
  --out-file OUT_FILE   Write the output of the command to the specified file instead of stdout.
  -v [{quiet,error,warning,notice,status,verbose,debug,v,trace,vv}]
                        Level of detail of the output. Valid options from less verbose to more verbose: -vquiet, -verror, -vwarning, -vnotice, -vstatus, -v or -vverbose, -vv or -vdebug, -vvv or -vtrace
  -cc CORE_CONF, --core-conf CORE_CONF
                        Define core configuration, overwriting global.conf values. E.g.: -cc core:non_interactive=True
  --project PROJECT     Project key for the Build Info in Artifactory
  --server SERVER       Server name of the Artifactory to get the build info from.
  --url URL             Artifactory url, like: https://<address>/artifactory.
  --user USER           User name for the Artifactory server.
  --password PASSWORD   Password for the Artifactory server.
  --token TOKEN         Token for the Artifactory server.
  --build-info BUILD_INFO
                        Name and number for the Build Info already published in Artifactory. You can add multiple Builds like --build-info=build_name,build_number --build-info=build_name,build_number
  --build-info-file BUILD_INFO_FILE
                        Path to the build-info file in your local folder. You can add multiple build-info files like --build-info=bi-1.json --build-info=bi-2.json
```

### ``conan art:build-info create``

```
$ usage: conan build-info create [-h] [-v [V]] [-cc CORE_CONF] [--server SERVER] [--url URL] [--user USER] [--password PASSWORD] [--token TOKEN] [--build-url BUILD_URL]
                               [--with-dependencies] [--add-cached-deps]
                               json build_name build_number repository [repository ...]

Creates BuildInfo from a Conan graph json. Refer to Conan documentation for commands that can output in that format.
(https://docs.conan.io/2/reference/commands/formatters/graph_info_json_formatter.html)

positional arguments:
  json                  Conan generated JSON output file.
  build_name            Build name property for BuildInfo.
  build_number          Build number property for BuildInfo.
  repository            Artifactory repository names. Accepts multiple values. Artifacts will be searched for in order.

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

### ``conan art:build-info bundle-create``

```
$ conan art:build-info bundle-create --help
usage: conan build-info bundle-create [-h] [-v [V]] [-cc CORE_CONF] [--server SERVER] [--url URL] [--user USER] [--password PASSWORD] [--token TOKEN]
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

### ``conan art:build-info bundle-delete``

```
$ conan art:build-info bundle-delete --help
usage: conan build-info bundle-delete [-h] [--out-file OUT_FILE] [-v [V]] [-cc CORE_CONF] [--server SERVER] [--url URL] [--user USER] [--password PASSWORD] [--token TOKEN]
                                      [--async {true,false}]
                                      bundle_name bundle_version

Deletes a Release Bundle v2 version and all its promotions. Both the Release Bundle attestation and all artifacts are removed.

positional arguments:
  bundle_name           The Release Bundle v2 name to delete.
  bundle_version        The Release Bundle v2 version to delete.

optional arguments:
  -h, --help            show this help message and exit
  --out-file OUT_FILE   Write the output of the command to the specified file instead of stdout.
  -v [V]                Level of detail of the output. Valid options from less verbose to more verbose: -vquiet, -verror, -vwarning, -vnotice, -vstatus, -v or -vverbose, -vv or -vdebug,
                        -vvv or -vtrace
  -cc CORE_CONF, --core-conf CORE_CONF
                        Define core configuration, overwriting global.conf values. E.g.: -cc core:non_interactive=True
  --server SERVER       Server name of the Artifactory to get the build info from.
  --url URL             Artifactory url, like: https://<address>/artifactory.
  --user USER           User name for the Artifactory server.
  --password PASSWORD   Password for the Artifactory server.
  --token TOKEN         Token for the Artifactory server.
  --async {true,false}  Determines whether the deletion is asynchronous (true) or synchronous (false). Default is true.
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
