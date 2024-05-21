## Installing hooks

To install just the hooks from this repository, without the other extensions, use the command:

`conan config install https://github.com/conan-io/conan-extensions.git -sf=extensions/hooks -tf=extensions/hooks`

The hooks are named so they won't be run by default, so we need to change the name of the hook
we want to use to start with `hook_`. As explained in the
[hooks documentation](https://docs.conan.io/2/reference/extensions/hooks.html).
To locate the path where the hook was placed, run the command `conan config home` to find
your local cache path and go to the `extensions/hooks` folder to rename the desired hook. Be aware that
the hooks will run everytime they are called unless disabled, which can be done by renaming the hook back to start with `_hook_`.

## PDBs hook
This hook copies the PDBs from their original location in the build folder to the package folder.
This is required for debugging libraries with Visual Studio when the original source files aren't present.
For more information on how to debug using the hook check the [documentation](https://docs.conan.io/2/examples/dev_flow/debug/debugging_visual.html)

### PDBs

A PDB has the information to link the source code of a debuggable object to the Visual Studio debugger. Each PDB is linked to a
specific file (executable or library) and contains the source file name and line numbers to display in the IDE.

When compiling shared libraries in Debug mode the created binary will contain the information of where the PDB will be
generated, which by default is the same path where the file is being compiled. The PDBs are created by the `cl.exe`
compiler with the `/Zi` flag, or by the `link.exe` when linking a DLL or executable.

PDBs are created when compiling a library or executable in Debug mode and are created by default in the same directory
as the file it is associated with. This means that when using Conan they will be created in the build directory in the
same path as the DLLs.

When using the Visual Studio debugger, it will look for PDBs to load in the following paths:

- The project folder.
- The original path where the associated file was compiled.
- The path where Visual is currently finding the compiled file, in our case the DLL in the package folder.

### Locating PDBs

To locate the PDB of a DLL we can use the `dumpbin.exe` tool, which comes with Visual by default and can be located
using the `vswhere` tool. PDBs will usually have the same name as its DLL, but it's not always the case, so checking
with the `dumpbin \PDBPATH` command makes sure we are getting the PDB corresponding to each DLL.

When a DLL is created it contains the information of the path where its corresponding PDB was generated. This can be
manually checked by running the following commands:
```
$ "%ProgramFiles(x86)%\Microsoft Visual Studio\Installer\vswhere.exe" -find "**\dumpbin.exe"
C:\Program Files\Microsoft Visual Studio\2022\Community\VC\Tools\MSVC\14.16.27023\bin\HostX64\x64\dumpbin.exe

# Use the path for the dumpbin.exe that you got from the previous command
$ "C:\Program Files\Microsoft Visual Studio\2022\Community\VC\Tools\MSVC\14.16.27023\bin\HostX64\x64\dumpbin.exe" /PDBPATH <dll_path>
...
Dump of file .\bin\zlib1.dll

File Type: DLL
PDB file found at 'C:\Users\{user}\.conan2\p\b\zlib78326f0099328\p\bin\zlib1.pdb'
...
```

### Source files

It is important to note that the PDB only contains the debug information, to debug through the actual file the source 
files are needed. These files have to be the exact same files as when the library was compiled and the PDB generated, 
as Visual Studio does a checksum check. In case where the build folder was deleted the source files from the source
folder can be used instead by telling Visual where to find them, as it is explained in the documentation.

### Static libraries

PDBs can sometimes be generated for LIB files, but for now the feature only focuses on shared libraries and
will only work with PDBs generated for DLLs. This is because the linking of PDBs and static libraries works differently
than with shared libraries and the PDBs are generated differently, which doesn't allow us to get the name and path
of a PDB through the `dumpbin` tool and will require different methods.
