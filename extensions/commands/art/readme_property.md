## [``conan art:property``](cmd_property.py)

```
$ conan art:property --help
usage: conan property [-h] [-v [V]] {add,set} ...

Manages Conan packages properties in Artifactory.

positional arguments:
  {add,set}   sub-command help
    add       Append properties for artifacts under a Conan reference recursively.
    set       Set properties for artifacts under a Conan reference.

options:
  -h, --help  show this help message and exit
  -v [V]      Level of detail of the output. Valid options from less verbose to more verbose: -vquiet,
              -verror, -vwarning, -vnotice, -vstatus, -v or -vverbose, -vv or -vdebug, -vvv or -vtrace
```

### conan art:property add

```
$ conan art:property add --help
usage: conan property add [-h] [-v [V]] [--server SERVER] [--url URL] [--user USER] [--password PASSWORD] [--property PROPERTY]
                          repository reference

Append properties for artifacts under a Conan reference recursively.

positional arguments:
  repository           Artifactory repository.
  reference            Conan reference.

options:
  -h, --help           show this help message and exit
  -v [V]               Level of detail of the output. Valid options from less verbose to more verbose: -vquiet, -verror, -vwarning, -vnotice,
                       -vstatus, -v or -vverbose, -vv or -vdebug, -vvv or -vtrace
  --server SERVER      Server name of the Artifactory to get the build info from
  --url URL            Artifactory url, like: https://<address>/artifactory
  --user USER          User name for the Artifactory server.
  --password PASSWORD  Password for the Artifactory server.
  --property PROPERTY  Property to add, like --property="build.name=buildname" --property="build.number=1"
```

### conan art:property set

```
$ conan art:property set --help
usage: conan property set [-h] [-v [V]] [--server SERVER] [--url URL] [--user USER] [--password PASSWORD] [--property PROPERTY] [--no-recursive]
                          repository reference

Set properties for artifacts under a Conan reference.

positional arguments:
  repository           Artifactory repository.
  reference            Conan reference.

options:
  -h, --help           show this help message and exit
  -v [V]               Level of detail of the output. Valid options from less verbose to more verbose: -vquiet, -verror, -vwarning, -vnotice,
                       -vstatus, -v or -vverbose, -vv or -vdebug, -vvv or -vtrace
  --server SERVER      Server name of the Artifactory to get the build info from
  --url URL            Artifactory url, like: https://<address>/artifactory
  --user USER          User name for the Artifactory repository.
  --password PASSWORD  Password for the Artifactory repository.
  --property PROPERTY  Property to add, like --property="build.name=buildname" --property="build.number=1"
  --no-recursive       Will not recursively set properties.
```