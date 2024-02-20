## Artifactory commands

> ⚠️ Warning: These custom commands are experimental. They are under development and are subject to breaking changes.

These are commands to manage certain Artifactory features:

- [``conan art:server``](readme_server.md): Manages Artifactory server urls and credentials.
  - ``add``
  -  ``list``
  -  ``remove``

- [``conan art:build-info``](readme_build_info.md): Manages JFrog Build Info (https://www.buildinfo.org/).
  - ``append``
  - ``create``
  - ``create-bundle``
  - ``delete``
  - ``get``
  - ``promote``
  - ``upload``

- [``conan art:property``](readme_property.md). Manages artifacts properties in Artifactory.
  - ``add``
  - ``set``


### How to manage Build Info's in Artifactory

#### 1. Configure your Artifactory server

Firstly, configure your Artifactory server with the url and credentials you want to use (this will come handy in the next commands):

```
conan art:server add my_artifactory --user=<user> --password=<pass>
```

#### 2. Create build infos for your binaries

Now, get a JSON output from a package build. This could come from a ``conan install`` or a ``conan create``:

```
conan create . --format json -s build_type=Release > create_release.json
conan create . --format json -s build_type=Debug > create_debug.json
```

Then upload the created package to your repository:

```
conan upload ... -c -r <conan-remote>
```

Using the generated JSON files you can create a Build Info JSON file. To do this, you need to provide the build
name and number. You will also need to indicate the artifactory server to use and the name of repository where the packages were uploaded in Artifactory (probably **not** the same one as the Conan remote name):

```
conan art:build-info create create_release.json mybuildname_release 1 <artifactory-repo> --server my_artifactory --with-dependencies > mybuildname_release.json
conan art:build-info create create_debug.json mybuildname_debug 1 <artifactory-repo> --server my_artifactory --with-dependencies > mybuildname_debug.json
```

### 3. Upload the build infos to your Artifactory server

Finally, you can upload the Build Info's:

```
conan art:build-info upload mybuildname_release.json --server my_artifactory
conan art:build-info upload mybuildname_debug.json <url> --server my_artifactory
```

### 4. Aggregate build infos into one

In this case we generated two Build Info's, for Release and Debug, but we can also merge those to
create a new Build Info that aggregates that information:

```
conan art:build-info append mybuildname_aggregated 1 --build-info=mybuildname_release,1 --build-info=mybuildname_debug,1 --server my_artifactory > mybuildname_aggregated.json
conan art:build-info upload mybuildname_aggregated.json --server my_artifactory"
```

This is handy in order to make promotions of packages from one repository to another in Artifactory.

### 5. Promote all the binaries of the aggregated build info

```
conan art:build-info promote mybuildname_aggregated 1 origin-artifactory-repo destination-artifactory-repo --server my_artifactory}
```

Now, both release and debug binaries from that pacakge ae available in the destination repository with just one command.

#### [conan art:promote](cmd_promote.py)

```
$ conan art:promote -h
usage: conan promote [-h] [-v [V]] [-cc CORE_CONF] --from ORIGIN --to
                     DESTINATION [--remote REMOTE] [--server SERVER]
                     [--url URL] [--user USER] [--password PASSWORD]
                     [--token TOKEN]
                     list

Promote a pkglist file from an origin Artifactory repository to a destination repository, without downloading the packages locally

positional arguments:
  list                  Package list file to promote

optional arguments:
  -h, --help            show this help message and exit
  -v [V]                Level of detail of the output. Valid options from less
                        verbose to more verbose: -vquiet, -verror, -vwarning,
                        -vnotice, -vstatus, -v or -vverbose, -vv or -vdebug,
                        -vvv or -vtrace
  -cc CORE_CONF, --core-conf CORE_CONF
                        Global configuration for Conan
  --from ORIGIN         Artifactory origin repository name
  --to DESTINATION      Artifactory destination repository name
  --remote REMOTE       Remote name to use for the origin repositories
  --server SERVER       Server name of the Artifactory server to promote from
                        if using art:property commands
  --url URL             Artifactory server url, like:
                        https://<address>/artifactory
  --user USER           User name for the repository
  --password PASSWORD   Password for the user name (instead of token)
  --token TOKEN         Token for the repository (instead of password)
```

Uses a pkglist file to promote a package from one Artifactory repository to another, without downloading the packages locally.
Needs a Pro license to work.
