## Artifactory commands

> ⚠️ Warning: These custom commands are experimental. They are under development and are subject to breaking changes.

These are commands to manage certain Artifactory features:

- ``conan art:server``. Manages Artifactory server urls and credentials

- ``conan art:build-info``. Manages JFROG BuildInfo

- ``conan art:property``. Manages artifacts properties in Artifactory

#### [conan art:server](cmd_server.py)

```
$ conan art:server --help
usage: conan server [-h] [-v [V]] {add,list,remove} ...

Manages Artifactory server and credentials.

positional arguments:
  {add,list,remove}  sub-command help
    add              Add Artifactory server and its credentials.
    list             List Artifactory servers.
    remove           Remove Artifactory servers.

options:
  -h, --help         show this help message and exit
  -v [V]             Level of detail of the output. Valid options from less verbose to more verbose: -vquiet,
                     -verror, -vwarning, -vnotice, -vstatus, -v or -vverbose, -vv or -vdebug, -vvv or -vtrace
```

#### [conan art:build-info](cmd_build_info.py)

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

#### [conan art:property](cmd_property.py)

```
$ conan art:property --help  
usage: conan property [-h] [-v [V]] {add,build-info-add,set} ...

Sets artifacts properties in Artifactory.

positional arguments:
  {add,build-info-add,set}
                        sub-command help
    add                 Append properties for artifacts under a Conan reference recursively.
    build-info-add      Load a Build Info JSON and add the build.number and build.name properties to all the artifacts present in the JSON.
    set                 Set properties for artifacts under a Conan reference recursively.

optional arguments:
  -h, --help            show this help message and exit
  -v [V]                Level of detail of the output. Valid options from less verbose to more verbose: -vquiet, -verror, -vwarning, -vnotice, -vstatus, -v or -vverbose, -vv or -vdebug, -vvv or
                        -vtrace
```

### Combining art:build-info and art:property to manage BuildInfo's in Artifactory

Firstly, configure your Artifactory server with the url and credentials you want to use (this will come handy in the next commands):

```
conan art:server add my_artifactory --user=<user> --password=<pass>
```

Now, get a JSON output from a package build. This could come from a ``conan install`` or a ``conan create``:

```
conan create . --format json -s build_type=Release > create_release.json
conan create . --format json -s build_type=Debug > create_debug.json
```

Then upload the created package to your repository:

```
conan upload ... -c -r ...
```

Using the generated JSON files you can create a Build Info JSON file. To do this, you need to provide the build
name and number. You will also need to indicate the artifactory server to use:

```
conan art:build-info create create_release.json mybuildname_release 1 <repo> --server my_artifactory --with-dependencies > mybuildname_release.json
conan art:build-info create create_debug.json mybuildname_debug 1 <repo> --server my_artifactory --with-dependencies > mybuildname_debug.json
```

Finally, you can upload the BuildInfo's:

```
conan art:build-info upload mybuildname_release.json --server my_artifactory
conan art:build-info upload mybuildname_debug.json <url> --server my_artifactory
```

In this case we generated two BuildInfo's, for Release and Debug, but we can also merge those to
create a new BuildInfo that aggregates that information:

```
conan art:build-info append mybuildname_aggregated 1 --build-info=mybuildname_release,1 --build-info=mybuildname_debug,1 --server my_artifactory > mybuildname_aggregated.json
conan art:build-info upload mybuildname_aggregated.json --server my_artifactory"
```

This is handy in order to make promotions of packages from one repository to another in Artifactory:

```
conan art:build-info promote mybuildname_aggregated 1 origin-repo destination-repo --server my_artifactory}
```

Now, both release and debug binaries from that pacakge ae available in the destination repository with just one command.
