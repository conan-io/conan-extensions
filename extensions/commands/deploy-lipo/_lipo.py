import os
import shutil
from subprocess import run


__all__ = ['is_macho_binary', 'lipo']

# These are for optimization only, to avoid unnecessarily reading files.
_binary_exts = ['.a', '.dylib']
_regular_exts = [
    '.h', '.hpp', '.hxx', '.c', '.cc', '.cxx', '.cpp', '.m', '.mm', '.txt', '.md', '.html', '.jpg', '.png'
]


def is_macho_binary(filename):
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


def copy_arch_file(src, dst, top=None, arch_folders=()):
    if os.path.isfile(src):
        if top and arch_folders and is_macho_binary(src):
            # Try to lipo all available archs on the first path.
            src_components = src.split(os.path.sep)
            top_components = top.split(os.path.sep)
            if src_components[:len(top_components)] == top_components:
                paths = [os.path.join(a, *(src_components[len(top_components):])) for a in arch_folders]
                paths = [p for p in paths if os.path.isfile(p)]
                if len(paths) > 1:
                    run(['lipo', '-output', dst, '-create'] + paths, check=True)
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

def lipo(dst_folder, arch_folders):
    for folder in arch_folders:
        graft_tree(folder,
                   dst_folder,
                   symlinks=True,
                   copy_function=lambda s, d, top=folder: copy_arch_file(s, d,
                                                                         top=top,
                                                                         arch_folders=arch_folders),
                   dirs_exist_ok=True)
