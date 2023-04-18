## Artifactory commands

> ⚠️ Warning: These custom commands are experimental. They are under development and are subject to breaking changes.

These are commands to manage certain Artifactory features:

- ``conan art:build-info``. Manages JFROG BuildInfo

- ``conan art:build-info``. Manages artifacts properties in Artifactory


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

First, get a JSON output from a package build. This could come from a ``conan install`` or a ``conan create``

```
conan create . --format json -s build_type=Release > create_release.json
conan create . --format json -s build_type=Debug > create_debug.json
```

Then upload the created package to your repository:

```
conan upload ... -c -r ...
```

Using the generated JSON files you can create a BuildInfo JSON. You have to pass the build
name and number and also the url and credentials for the Artifactory repository:

```
conan art:build-info create create_release.json mybuildname_release 1 --url=<url> --user=<user> --password=<pass> --repository=<repo> > mybuildname_release.json
conan art:build-info create create_debug.json mybuildname_debug 1 --url=<url> --user=<user> --password=<pass> --repository=<repo> > mybuildname_debug.json
```

You have to set the properties for the uploaded artifacts so they are linked to the BuildInfo in Artifactory:

```
conan art:property build-info-add mybuildname_release.json <url> <repo> --user=<user> --password=<pass>
conan art:property build-info-add mybuildname_debug.json <url> <repo> --user=<user> --password=<pass>
```

Finally, you can upload the BuildInfo's

```
conan art:build-info upload mybuildname_release.json <url> --user=<user> --password=<pass>
conan art:build-info upload mybuildname_debug.json <url> --user=<user> --password=<pass>
```

In this case we generated two BuilInfo's, for Release and Debug, we can merge those to
create a new aggregated BuildInfo that we also will upload and set properties to:

```
conan art:build-info append mybuildname_aggregated 1 --build-info=mybuildname_release.json --build-info=mybuildname_debug.json > mybuildname_aggregated.json
conan art:build-info upload mybuildname_aggregated.json <url> --user=<user> --password="<pass>"
conan art:property build-info-add mybuildname_aggregated.json <url> <repo> --user=<user> --password="<pass>"
```
