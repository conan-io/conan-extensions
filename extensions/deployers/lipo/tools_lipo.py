import os
import shlex
import shutil
from subprocess import Popen

from conan.errors import ConanException


__all__ = ['is_macho_binary', 'lipo']

# These are for optimization only, to avoid unnecessarily reading files.
_binary_exts = ['.a', '.dylib']
_regular_exts = [
    '.h', '.hpp', '.hxx', '.c', '.cc', '.cxx', '.cpp', '.m', '.mm', '.txt', '.md', '.html', '.jpg', '.png'
]


def lipo(conanfile, command='create', output=None, inputs=(), arch_type=None, arch_types=()):
    """
    Run lipo for one or more files (see lipo manpage)
    Arguments:
      conanfile
      command: one of
        archs
        create
        detailed_info
        extract
        extract_family
        info
        remove
        replace
        thin
        verify
      output: output file (not used by all commands)
      inputs: one or more input files
      arch_type: architecture, if required
      arch_types: multiple architectures, if required
    """
    archs = arch_types or ([arch_type] if arch_type else [])
    if len(inputs) != 1 and command not in ('create', 'detailed_info', 'info', 'replace'):
        raise ConanException(f'lipo {command} requires exactly one input file')
    if len(archs) != 1 and command in ('thin',):
        raise ConanException(f'lipo {command} requires exactly one arch_type')
    if archs and command not in ('extract', 'extract_family', 'remove', 'replace', 'verify_arch'):
        raise ConanException(f'lipo {command} does not require arch_type')
    cmd = ['lipo'] + list(inputs) + [f"-{command}"]
    if command in ('archs', 'detailed_info', 'info', 'verify_arch'):
        return Popen(cmd)
    elif command == 'verify_arch':
        return Popen(cmd + list(archs))
    if not output:
        raise ConanException('lipo output is required')
    cmd_output = ['-output', output]
    if command == 'create':
        conanfile.run(shlex.join(cmd + cmd_output))
    elif command in ('extract', 'extract_family', 'remove'):
        cmd = cmd[:-1] # remove command
        for arch in archs:
            cmd += [f"-{command}", arch]
        conanfile.run(shlex.join(cmd + cmd_output))
    elif command == 'replace':
        if len(archs) + 1 != len(inputs):
            raise ConanException(f'lipo {command} requires exactly one arch_type per input and one universal input')
        cmd = ['lipo', inputs[0]]
        for i in range(len(archs)):
            cmd += [f"-{command}", archs[i], inputs[i + 1]]
        conanfile.run(shlex.join(cmd + cmd_output))
    elif command == 'thin':
        conanfile.run(shlex.join(cmd + list(archs) + cmd_output))
    else:
        raise ConanException(f'lipo {command} is not a valid command')


def is_macho_binary(filename):
    """
    Determines if filename is a Mach-O binary or fat binary
    """
    ext = os.path.splitext(filename)[1]
    if ext in _binary_exts:
        return True
    if ext in _regular_exts:
        return False
    with open(filename, "rb") as f:
        header = f.read(4)
        if header == b'\xcf\xfa\xed\xfe':
            # cffaedfe is Mach-O binary
            return True
        elif header == b'\xca\xfe\xba\xbe':
            # cafebabe is Mach-O fat binary
            return True
        elif header == b'!<arch>\n':
            # ar archive
            return True
    return False


def copy_arch_file(conanfile, src, dst, top=None, arch_folders=(), add=False):
    if os.path.isfile(src):
        if top and arch_folders and is_macho_binary(src):
            # Try to lipo all available archs on the first path.
            src_components = src.split(os.path.sep)
            top_components = top.split(os.path.sep)
            if src_components[:len(top_components)] == top_components:
                paths = [os.path.join(a, *(src_components[len(top_components):])) for a in arch_folders]
                paths = [p for p in paths if os.path.isfile(p)]
                if len(paths) > 1 or add:
                    if add and os.path.exists(dst):
                        lipo(conanfile, 'create', output=dst, inputs=[dst] + paths)
                    else:
                        lipo(conanfile, 'create', output=dst, inputs=paths)
                    return
        if os.path.exists(dst):
            pass # don't overwrite existing files
        else:
            shutil.copy2(src, dst)


# Modified copytree to copy new files to an existing tree.
def graft_tree(src, dst, symlinks=False, copy_function=shutil.copy2, dirs_exist_ok=False):
    names = os.listdir(src)
    os.makedirs(dst, exist_ok=dirs_exist_ok)
    errors = []
    for name in names:
        srcname = os.path.join(src, name)
        dstname = os.path.join(dst, name)
        try:
            if symlinks and os.path.islink(srcname):
                if os.path.exists(dstname):
                    continue
                linkto = os.readlink(srcname)
                os.symlink(linkto, dstname)
            elif os.path.isdir(srcname):
                graft_tree(srcname, dstname, symlinks, copy_function, dirs_exist_ok)
            else:
                copy_function(srcname, dstname)
            # What about devices, sockets etc.?
        # catch the Error from the recursive graft_tree so that we can
        # continue with other files
        except shutil.Error as err:
            errors.extend(err.args[0])
        except OSError as why:
            errors.append((srcname, dstname, str(why)))
    try:
        shutil.copystat(src, dst)
    except OSError as why:
        # can't copy file access times on Windows
        if why.winerror is None: # pylint: disable=no-member
            errors.extend((src, dst, str(why)))
    if errors:
        raise shutil.Error(errors)

def lipo_tree(conanfile, dst_folder, arch_folders, add=False):
    if add:
        copy_function = lambda s, d: copy_arch_file(conanfile, s, d,
                                                    top=folder,
                                                    arch_folders=arch_folders,
                                                    add=True)
    else:
        copy_function = lambda s, d: copy_arch_file(conanfile, s, d,
                                                    top=folder,
                                                    arch_folders=arch_folders)
    for folder in arch_folders:
        graft_tree(folder,
                   dst_folder,
                   symlinks=True,
                   copy_function=copy_function,
                   dirs_exist_ok=True)
