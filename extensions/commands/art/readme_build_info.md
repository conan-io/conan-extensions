## [``conan art:build-info``](cmd_build_info.py)

```
$ conan art:build-info --help
usage: conan build-info [-h] [-v [V]] {append,create,delete,get,promote,upload} ...

Manages JFROG BuildInfo

positional arguments:
  {append,create,delete,get,promote,upload}
                        sub-command help
    append              Append published build to the build info.
    create              Creates BuildInfo from a Conan graph json from a conan install or create.
    delete              Removes builds stored in Artifactory. Useful for cleaning up old build info data.
    get                 Get Build Info information.
    promote             Promote the BuildInfo from the source to the target repository.
    upload              Uploads BuildInfo json to repository.

optional arguments:
  -h, --help            show this help message and exit
  -v [V]                Level of detail of the output. Valid options from less verbose to more verbose: -vquiet, -verror, -vwarning, -vnotice, -vstatus, -v or -vverbose, -vv or -vdebug, -vvv or
                        -vtrace
```

### ``conan art:build-info append``

```
$ conan art:build-info append --help
usage: conan build-info append [-h] [-v [V]] [--project PROJECT] [--server SERVER] [--url URL]
                               [--user USER] [--password PASSWORD] [--build-info BUILD_INFO]
                               build_name build_number

Append published build to the build info.

positional arguments:
  build_name            The current build name.
  build_number          The current build number.

options:
  -h, --help            show this help message and exit
  -v [V]                Level of detail of the output. Valid options from less verbose to more
                        verbose: -vquiet, -verror, -vwarning, -vnotice, -vstatus, -v or -vverbose, -vv
                        or -vdebug, -vvv or -vtrace
  --project PROJECT     Project key for the Build Info in Artifactory
  --server SERVER       Server name of the Artifactory to get the build info from.
  --url URL             Artifactory url, like: https://<address>/artifactory.
  --user USER           User name for the Artifactory server.
  --password PASSWORD   Password for the Artifactory server.
  --build-info BUILD_INFO
                        Name and number for the Build Info already published in Artifactory. You can
                        add multiple Builds like --build-info=build_name,build_number --build-
                        info=build_name,build_number
```

### ``conan art:build-info create``

```
$ conan art:build-info create --help
usage: conan build-info create [-h] [-v [V]] [--server SERVER] [--url URL] [--user USER]
                               [--password PASSWORD] [--with-dependencies]
                               json build_name build_number repository

Creates BuildInfo from a Conan graph json from a conan install or create.

positional arguments:
  json                 Conan generated JSON output file.
  build_name           Build name property for BuildInfo.
  build_number         Build number property for BuildInfo.
  build_url            Build url property for BuildInfo.
  repository           Artifactory repository name where artifacts are located -not the conan remote name-.

options:
  -h, --help           show this help message and exit
  -v [V]               Level of detail of the output. Valid options from less verbose to more verbose:
                       -vquiet, -verror, -vwarning, -vnotice, -vstatus, -v or -vverbose, -vv or
                       -vdebug, -vvv or -vtrace
  --server SERVER      Server name of the Artifactory to get the build info from.
  --url URL            Artifactory url, like: https://<address>/artifactory. This may be not necessary
                       if all the information for the Conan artifacts is present in the local cache.
  --user USER          User name for the Artifactory server.
  --password PASSWORD  Password for the Artifactory server.
  --with-dependencies  Whether to add dependencies information or not. Default: false.
```

### ``conan art:build-info create-bundle``

```
$ conan art:build-info create-bundle --help
usage: conan build-info create-bundle [-h] [-v [V]] [--server SERVER] [--url URL] [--user USER]
                                      [--password PASSWORD]
                                      json repository bundle_name bundle_version sign_key_name

Creates an Artifactory Release Bundle from the information of the Build Info

positional arguments:
  json                 BuildInfo JSON.
  repository           Artifactory repository where artifacts are located.
  bundle_name          The created bundle name.
  bundle_version       The created bundle version.
  sign_key_name        Signing Key name.

options:
  -h, --help           show this help message and exit
  -v [V]               Level of detail of the output. Valid options from less verbose to more verbose:
                       -vquiet, -verror, -vwarning, -vnotice, -vstatus, -v or -vverbose, -vv or
                       -vdebug, -vvv or -vtrace
  --server SERVER      Server name of the Artifactory to get the build info from.
  --url URL            Artifactory url, like: https://<address>/artifactory.
  --user USER          User name for the Artifactory server.
  --password PASSWORD  Password for the Artifactory server.
```

### ``conan art:build-info delete``

```
$ conan art:build-info delete --help
usage: conan build-info delete [-h] [-v [V]] [--project PROJECT] [--server SERVER] [--url URL]
                               [--user USER] [--password PASSWORD] [--build-number BUILD_NUMBER]
                               [--delete-artifacts] [--delete-all]
                               build_name

Removes builds stored in Artifactory. Useful for cleaning up old build info data.

positional arguments:
  build_name            BuildInfo name to delete.

options:
  -h, --help            show this help message and exit
  -v [V]                Level of detail of the output. Valid options from less verbose to more
                        verbose: -vquiet, -verror, -vwarning, -vnotice, -vstatus, -v or -vverbose, -vv
                        or -vdebug, -vvv or -vtrace
  --project PROJECT     Project key for the Build Info in Artifactory
  --server SERVER       Server name of the Artifactory to get the build info from.
  --url URL             Artifactory url, like: https://<address>/artifactory.
  --user USER           User name for the Artifactory server.
  --password PASSWORD   Password for the Artifactory server.
  --build-number BUILD_NUMBER
                        BuildInfo numbers to promote. You can add several build-numbers for the same
                        build-name, like: --build-number=1 --build-number=2.
  --delete-artifacts    Build artifacts are also removed provided they have the corresponding
                        build.name and build.number properties attached to them. Default false.
  --delete-all          The whole build is removed. Default false.
```

### ``conan art:build-info get``

```
$ conan art:build-info get --help
usage: conan build-info get [-h] [-v [V]] [--project PROJECT] [--server SERVER] [--url URL]
                            [--user USER] [--password PASSWORD]
                            build_name build_number

Get Build Info information.

positional arguments:
  build_name           BuildInfo name to get.
  build_number         BuildInfo number to get.

options:
  -h, --help           show this help message and exit
  -v [V]               Level of detail of the output. Valid options from less verbose to more verbose:
                       -vquiet, -verror, -vwarning, -vnotice, -vstatus, -v or -vverbose, -vv or
                       -vdebug, -vvv or -vtrace
  --project PROJECT    Project key for the Build Info in Artifactory
  --server SERVER      Server name of the Artifactory to get the build info from.
  --url URL            Artifactory url, like: https://<address>/artifactory.
  --user USER          User name for the Artifactory server.
  --password PASSWORD  Password for the Artifactory server.
```

### ``conan art:build-info promote``

```
$ conan art:build-info promote --help
usage: conan build-info promote [-h] [-v [V]] [--project PROJECT] [--server SERVER] [--url URL]
                                [--user USER] [--password PASSWORD] [--dependencies]
                                [--comment COMMENT]
                                build_name build_number source_repo target_repo

Promote the BuildInfo from the source to the target repository.

positional arguments:
  build_name           BuildInfo name to promote.
  build_number         BuildInfo number to promote.
  source_repo          Artifactory repository to get artifacts from.
  target_repo          Artifactory repository to promote artifacts to.

options:
  -h, --help           show this help message and exit
  -v [V]               Level of detail of the output. Valid options from less verbose to more verbose:
                       -vquiet, -verror, -vwarning, -vnotice, -vstatus, -v or -vverbose, -vv or
                       -vdebug, -vvv or -vtrace
  --project PROJECT    Project key for the Build Info in Artifactory
  --server SERVER      Server name of the Artifactory to get the build info from.
  --url URL            Artifactory url, like: https://<address>/artifactory.
  --user USER          User name for the Artifactory server.
  --password PASSWORD  Password for the Artifactory server.
  --dependencies       Whether to copy the build's dependencies or not. Default: false.
  --comment COMMENT    An optional comment describing the reason for promotion. Default: ''
```

### ``conan art:build-info upload``

```
$ conan art:build-info upload --help
usage: conan build-info upload [-h] [-v [V]] [--project PROJECT] [--server SERVER] [--url URL]
                               [--user USER] [--password PASSWORD]
                               build_info

Uploads BuildInfo json to repository.

positional arguments:
  build_info           BuildInfo json file.

options:
  -h, --help           show this help message and exit
  -v [V]               Level of detail of the output. Valid options from less verbose to more verbose:
                       -vquiet, -verror, -vwarning, -vnotice, -vstatus, -v or -vverbose, -vv or
                       -vdebug, -vvv or -vtrace
  --project PROJECT    Project key for the Build Info in Artifactory
  --server SERVER      Server name of the Artifactory to get the build info from.
  --url URL            Artifactory url, like: https://<address>/artifactory.
  --user USER          User name for the Artifactory server.
  --password PASSWORD  Password for the Artifactory server.
```