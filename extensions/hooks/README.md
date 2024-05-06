## PDBs hook
This hook copies the PDBs from their original location in the build folder to the package folder.
This is required for debugging libraries with Visual Studio when the original source files aren't present.
For more information on how to debug using the hook check the [documentation](https://docs.conan.io/2/examples/dev_flow/debug/debugging_visual.html)

### PDBs and how lo locate them

A PDB has the information to link the source code of a debuggable object to the Visual Studio debugger. Each PDB is linked to a
specific file (executable or library) and contains the source file name and line numbers to display in the IDE.

When compiling shared libraries in Debug mode the created binary will contain the information of where the PDB will be
generated, which by default is the same path where the file is being compiled. The PDBs are created by the ``cl.exe``
compiler with the ``/Zi`` flag, or by the ``link.exe`` when linking a DLL or executable.

To locate the PDB of a DLL we can use the ``dumpbin.exe`` tool, which comes with Visual by default and can be located
using the ``vswhere`` tool. PDBs will usually have the same name as it's 
DLL, but it's not always the case, so checking with the ``dumpbin \PDBPATH`` command makes sure we are getting the PDB
corresponding to each DLL. 

PDBs are created when compiling a library or executable in Debug mode and are created by default in the same directory
as the file it is associated with. This means that when using Conan they will be created in the build directory in the
same path as the DLLs.

When using the Visual Studio debugger, it will look for PDBs to load in the following paths:

- The project folder.
- The original path where the associated file was compiled.
- The path where Visual is currently finding the compiled file, in our case the DLL in the package folder.

The hook copies the PDBs to the package folder next to the DLL so Visual will find it there when loading its debug symbols.

#### Source files

It is important to note that the PDB only contains the debug information, to debug through the actual file the source 
files are needed. These files have to be the exact same files as when the library was compiled and the PDB generated, 
as Visual Studio does a checksum check. In case where the build folder was deleted the source files from the source
folder can be used instead by telling Visual where to find them, as it is explained in the documentation.

#### Static libraries

The hook will only work for shared libraries for now because the linking of PDBs and static libraries works differently
than with shared libraries. This means that we can't make sure that the PDBs are generated in the same way and the
current implementation will work for them. Also, we can't get the name and path of the PDB through the ``dumpbin`` tool
so we only recommend this hook for use with dependencies built as shared.
