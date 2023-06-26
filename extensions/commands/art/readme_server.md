## [``conan art:server``](cmd_server.py)

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

### ``conan art:server add``

```
$ conan art:server add --help
usage: conan server add [-h] [-v [V]] [--user USER] [--password PASSWORD] name url

Add Artifactory server and its credentials.

positional arguments:
  name                 Name of the server
  url                  URL of the artifactory server

options:
  -h, --help           show this help message and exit
  -v [V]               Level of detail of the output. Valid options from less verbose to more verbose:
                       -vquiet, -verror, -vwarning, -vnotice, -vstatus, -v or -vverbose, -vv or
                       -vdebug, -vvv or -vtrace
  --user USER          user name for the repository
  --password PASSWORD  password for the user name
```

Example:

```
$ conan art:server add myartifactory https://my.artifactory.com/artifactory --user user --password password
```

### ``conan art:server list``

```
$ conan art:server list --help
usage: conan server list [-h] [-f FORMAT] [-v [V]]

List Artifactory servers.

options:
  -h, --help            show this help message and exit
  -f FORMAT, --format FORMAT
                        Select the output format: json
  -v [V]                Level of detail of the output. Valid options from less verbose to more
                        verbose: -vquiet, -verror, -vwarning, -vnotice, -vstatus, -v or -vverbose, -vv
                        or -vdebug, -vvv or -vtrace
```

Example:

```
$ conan art:server list

myartifactory:
  url: https://my.artifactory.com/artifactory
  user: user
  password: *******
```

### ``conan art:server remove``

```
$ conan art:server remove --help
usage: conan server remove [-h] [-v [V]] name

Remove Artifactory servers.

positional arguments:
  name        Name of the server

options:
  -h, --help  show this help message and exit
  -v [V]      Level of detail of the output. Valid options from less verbose to more verbose: -vquiet,
              -verror, -vwarning, -vnotice, -vstatus, -v or -vverbose, -vv or -vdebug, -vvv or -vtrace
```

Example:

```
$ conan art:server remove myartifactory

Server 'myartifactory' (https://my.artifactory.com/artifactory) removed successfully
```
