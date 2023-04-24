## Misc commands
Commands that extend Conan in one way or another without fitting in a nice category

#### [Promote graph](cmd_promote_graph.py)

Promotes the dependency graph of a reference from one remote to another



**Parameters**

```
positional arguments:
  path                  Path to a folder containing a conanfile

options:
  -h, --help            show this help message and exit
  -v [V]                Level of detail of the output. Valid options from less verbose to more verbose: -vquiet, -verror, -vwarning, -vnotice,
                        -vstatus, -v or -vverbose, -vv or -vdebug, -vvv or -vtrace
  --remote-origin REMOTE_ORIGIN
                        Origin remote to copy from
  --remote-dest REMOTE_DEST
                        Destination remote to copy to
  --name NAME           Provide a package name if not specified in conanfile
  --version VERSION     Provide a package version if not specified in conanfile
  --user USER           Provide a user if not specified in conanfile
  --channel CHANNEL     Provide a channel if not specified in conanfile
  -l LOCKFILE, --lockfile LOCKFILE
                        Path to a lockfile. Use --lockfile="" to avoid automatic use of existing 'conan.lock' file
  --lockfile-partial    Do not raise an error if some dependency is not found in lockfile
  --build-require       Whether the provided reference is a build-require
  --only-recipe         Download only the recipe/s, not the binary packages.
  -p PACKAGE_QUERY, --package-query PACKAGE_QUERY
                        Only download packages matching a specific query. e.g: os=Windows AND (arch=x86 OR compiler=gcc)
  -o OPTIONS_HOST, --options OPTIONS_HOST
                        Define options values (host machine), e.g.: -o Pkg:with_qt=true
  -o:b OPTIONS_BUILD, --options:build OPTIONS_BUILD
                        Define options values (build machine), e.g.: -o:b Pkg:with_qt=true
  -o:h OPTIONS_HOST, --options:host OPTIONS_HOST
                        Define options values (host machine), e.g.: -o:h Pkg:with_qt=true
  -pr PROFILE_HOST, --profile PROFILE_HOST
                        Apply the specified profile to the host machine
  -pr:b PROFILE_BUILD, --profile:build PROFILE_BUILD
                        Apply the specified profile to the build machine
  -pr:h PROFILE_HOST, --profile:host PROFILE_HOST
                        Apply the specified profile to the host machine
  -s SETTINGS_HOST, --settings SETTINGS_HOST
                        Settings to build the package, overwriting the defaults (host machine). e.g.: -s compiler=gcc
  -s:b SETTINGS_BUILD, --settings:build SETTINGS_BUILD
                        Settings to build the package, overwriting the defaults (build machine). e.g.: -s:b compiler=gcc
  -s:h SETTINGS_HOST, --settings:host SETTINGS_HOST
                        Settings to build the package, overwriting the defaults (host machine). e.g.: -s:h compiler=gcc
  -c CONF_HOST, --conf CONF_HOST
                        Configuration to build the package, overwriting the defaults (host machine). e.g.: -c
                        tools.cmake.cmaketoolchain:generator=Xcode
  -c:b CONF_BUILD, --conf:build CONF_BUILD
                        Configuration to build the package, overwriting the defaults (build machine). e.g.: -c:b
                        tools.cmake.cmaketoolchain:generator=Xcode
  -c:h CONF_HOST, --conf:host CONF_HOST
                        Configuration to build the package, overwriting the defaults (host machine). e.g.: -c:h
                        tools.cmake.cmaketoolchain:generator=Xcode
```

An example usage of this command is:

`conan misc:promote-graph recipes/gstreamer/conanfile.py --remote-origin conancenter --remote-dest myremote -pr:h my_host_profile -pr:b my_build_profile`

Note that only the dependencies necessary for the current configuration will be computed and promoted.
It's possible that you might need to run this command several times with different profiles to gather all your wanted dependencies.