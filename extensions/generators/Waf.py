import os
from conan.internal import check_duplicated_generator
from conans.util.files import save

class Waf(object):
    def __init__(self, conanfile):
        self.conanfile = conanfile

    def get_use_name(self, ref_name, parent_ref = None):
        """
            see: https://github.com/conan-io/conan/issues/13611#issuecomment-1496300127

                * <pkg>::<pkg> refers to ALL components in a package
                * <comp> refers to a component in the current package
                * <pkg>::<comp> refers to a component in another package
        """
        assert(type(ref_name) is str)
        assert(not parent_ref or type(parent_ref) is str)
        if '::' in ref_name:
            sp = ref_name.split('::')
            if sp[0] == sp[1]:
                ref_name = sp[0]
            else:
                assert(len(sp[0])>0) #Conan bug?
                ref_name = '_'.join(sp)
        elif parent_ref:
            ref_name = f'{parent_ref}_{ref_name}'
        return ref_name \
            .replace('-', '_') \
            .replace('+','p') #"flac::libflac++" -> "flac_libflacpp"

    def generate(self):
        check_duplicated_generator(self, self.conanfile)

        output = self.gen_deps()

        #add settings, which will be interpreted and applied at configuration time
        settings = self.conanfile.settings.serialize()
        print(settings)
        output.update({
            "CONAN_SETTINGS": settings,
            #paths that should be added to sys.path (only waf tools currently)
            "DEP_SYS_PATHS": self._get_waftools_paths(),
            #global Conan config/flags
            "CONAN_CONFIG": self._get_conan_config()
        })

        filename = os.path.join(
            self.conanfile.generators_folder,
            "conan_deps.py"
        )

        set_conan_to_waf_arch(settings, output)
        set_conan_to_waf_os(settings, output)
        set_conan_to_waf_compiler(settings, output)

        deps = []
        for k,v in output.items():
            if type(v) is str:
                deps.append(f'conf.env.{k} = "{v}"')
            else:
                deps.append(f'conf.env.{k} = {v}')

        #python syspath from deps (for distributing waf tools as conan packages)
        syspaths = []
        for p in output['DEP_SYS_PATHS']:
            syspaths.append(f'"{p}",')

        save(filename, waftool_src_template % (
            'sys.path = [\n    %s\n]+sys.path' % '\n    '.join(syspaths),
            '\n    '.join(deps),
        ))

    def gen_usedeps(self):
        """
            Generate CONAN_USE_<x> vars for all components and packages
        """
        out = {}

        def resolve_pkg(req, dep):
            usename = self.get_use_name(dep.ref.name, dep.ref.name)
            comp_deps = []
            pkg_deps = []
            if dep.has_components:
                comp_deps = list(reversed(dep.cpp_info.get_sorted_components()))

    def gen_deps(self):
        out = {
            "ALL_CONAN_PACKAGES": [],
            "ALL_CONAN_PACKAGES_BUILD": [],
        }
        depmap_host = {}
        depmap_build = {}

        for req, dep in self.conanfile.dependencies.items():
            # print(dep.ref, f", direct={req.direct}, build={req.build}")
            depmap = depmap_build if req.build else depmap_host

            if dep.cpp_info.has_components:
                comp_depnames = []
                #generate "pkg::comp" for each comp
                comps = dep.cpp_info.get_sorted_components().items()
                for ref_name, cpp_info in comps:
                    use_name = self.get_use_name(ref_name, dep.ref.name)
                    comp_depnames.append(use_name)
                    depmap[use_name] = {
                        'build': req.build,
                        'cpp_info': cpp_info,
                        'usename': use_name,
                        'requires': [self.get_use_name(c, dep.ref.name) for c in cpp_info.requires],
                        'package': self.get_use_name(dep.ref.name),
                        'buildenv_info': dep.buildenv_info,
                        'runenv_info': dep.runenv_info,
                    }

                #generate a parent "pkg::pkg"
                use_name = self.get_use_name(dep.ref.name)
                depmap[use_name] = {
                    'build': req.build,
                    'cpp_info': dep.cpp_info,
                    'usename': use_name,
                    'requires': comp_depnames,
                    'package': self.get_use_name(dep.ref.name),
                    'buildenv_info': dep.buildenv_info,
                    'runenv_info': dep.runenv_info,
                }
            else:
                #only generate "pkg"
                use_name = self.get_use_name(dep.ref.name)
                depmap[use_name] = {
                    'build': req.build,
                    'cpp_info': dep.cpp_info,
                    'usename': use_name,
                    'requires': [self.get_use_name(c, dep.ref.name) for c in dep.cpp_info.requires],
                    'package': use_name,
                    'buildenv_info': dep.buildenv_info,
                    'runenv_info': dep.runenv_info,
                }

        def toposort_deps(self, depmap, root, i):
            out = []
            def visit(n):
                if n.get('__visited', 0) == i:
                    return
                assert n.get('__at', 0) != i, "Cyclic dependencies!\n\tusename: %s\n\trequires: %s" % (n['usename'], n['requires'])
                n['__at'] = i
                for req in n['requires']:
                    if req not in depmap:
                        continue
                    # assert req in depmap, "The following dependency for '%s' wasn't found: '%s'\n\tis the package broken, or am I broken?" % (n['usename'], req)
                    visit(depmap[req])
                n['__at'] = 0
                n['__visited'] = i
                out.append(n)
            visit(root)
            return out

        sortit = 0

        #generate host dep info (includes, flags, etc)
        for name, info in depmap_host.items():
            sortit += 1
            sorted_deps = toposort_deps(self, depmap_host, info, sortit)
            info['use'] = list(reversed(sorted_deps))
            self.proc_cpp_info(info, out)

        #collect bindirs
        buildenv = {}
        for name, info in depmap_build.items():
            sortit += 1
            sorted_deps = toposort_deps(self, depmap_build, info, sortit)
            info['use'] = list(reversed(sorted_deps))
            self.proc_cpp_info(info, out)

            #add buildenv info
            buildenv.update(info['buildenv_info'].vars(self.conanfile, scope="build"))

        buildenv['PATH'] = os.pathsep.join(out.get('CONAN_BUILD_BIN_PATH', set()) | {'$PATH'})
        buildenv['LD_LIBRARY_PATH'] = os.pathsep.join(out.get('CONAN_BUILD_LIB_PATH', set()))
        buildenv['DYLD_LIBRARY_PATH'] = os.pathsep.join(out.get('CONAN_BUILD_LIB_PATH', set()))

        out['CONAN_BUILDENV'] = buildenv

        return out

    def proc_cpp_info(self, depinfo, out):
        name = depinfo['usename']
        pkg_name = depinfo['package']
        cpp_info = depinfo['cpp_info']

        def setvar(k, v):
            if v:
                out[f"{k}_{name}"] = v

        def setpath(k, v):
            #convert relative paths from conan to absolute
            if type(v) is list:
                ret = [os.path.abspath(p) for p in v]
                setvar(k, ret)
                return ret
            else:
                assert type(v) is str
                ret = [os.path.abspath(v)]
                setvar(k, ret[0])
                return ret

        if depinfo['build']:            
            #add 'build_' prefix to all usenames for build items
            #avoids name conflicts while making build graph available in scripts
            name = f'build_{name}'

            out["ALL_CONAN_PACKAGES_BUILD"].append(name)
            #CONAN_USE is used by waftool to expand deps for usenames

            setvar('CONAN_USE', ['build_%s' % d['usename'] for d in depinfo['use']])

            #process build dependencies
            abs_bindirs = setpath("BINPATH", cpp_info.bindirs)
            if 'CONAN_BUILD_BIN_PATH' not in out:
                out['CONAN_BUILD_BIN_PATH'] = set()
            out['CONAN_BUILD_BIN_PATH'].update(abs_bindirs)

            abs_libdirs = setpath("LIBPATH", cpp_info.bindirs)
            if 'CONAN_BUILD_LIB_PATH' not in out:
                out['CONAN_BUILD_LIB_PATH'] = set()
            out['CONAN_BUILD_LIB_PATH'].update(abs_libdirs)
        else:
            #process host dependencies
            out["ALL_CONAN_PACKAGES"].append(name)
            
            #CONAN_USE is used by waftool to expand deps for usenames
            setvar('CONAN_USE', [d['usename'] for d in depinfo['use']])

        libs = cpp_info.libs + cpp_info.system_libs + cpp_info.objects
        
        #warning: default waf C/C++ tasks don't distinguish between exelink and
        #sharedlink; will need to override `run_str`. For reference, see:
        #`waflib.Tools.cxx.cxxshlib`. this could be handled by a waftool if it's
        #ever needed

        linkflags = list(set(cpp_info.sharedlinkflags + cpp_info.exelinkflags))
        setvar("LINKFLAGS", linkflags)
        setvar("LIB", libs)
        setpath("LIBPATH", cpp_info.libdirs)
        setvar("CFLAGS", cpp_info.cflags)
        setvar("CXXFLAGS", cpp_info.cxxflags)
        setvar("INCLUDES", cpp_info.includedirs)
        setvar("DEFINES", cpp_info.defines)
        setvar("FRAMEWORK", cpp_info.frameworks)
        setpath("FRAMEWORKPATH", cpp_info.frameworkdirs)

        #Extra non-waf variables from Conan cpp_info
        setpath("SRCPATH", cpp_info.srcdirs)
        setpath("RESPATH", cpp_info.resdirs)
        setpath("BUILDPATH", cpp_info.builddirs)
        setpath("BINPATH", cpp_info.bindirs)

        #Unused waf variables:
        # "ARCH"
        # "STLIB"
        # "STLIBPATH"
        # "LDFLAGS"
        # "RPATH"
        # "CPPFLAGS"

    def _get_conan_config(self):
        conf_info = self.conanfile.conf
        out = {
            "CFLAGS": conf_info.get('tools.build:cflags', [], check_type=list),
            
            "CXXFLAGS": conf_info.get('tools.build:cxxflags', [], check_type=list),
            
            "DEFINES": conf_info.get('tools.build:defines', [], check_type=list),
            
            "LINKFLAGS":
                conf_info.get('tools.build:exelinkflags', [], check_type=list) +
                conf_info.get('tools.build:sharedlinkflags', [], check_type=list),
        }
        return out

    def _get_waftools_paths(self):
        #enables distributing waf tools inside of conan packages
        #e.g. add a waf tool to the 'flatbuffers' package so that you can use
        #the flatc compiler from wscripts, and not worry about versioning
        out = []
        for require, dependency in self.conanfile.dependencies.items():
            if not require.build:
                continue #only find waf tools from build environment
            envvars = dependency.buildenv_info.vars(self.conanfile, scope="build")
            if "WAF_TOOLS" not in envvars.keys():
                continue

            tools = envvars["WAF_TOOLS"].split(" ")
            for entry in tools:
                if not os.path.exists(entry):
                    self.outputs.warn(f"Waf tool entry not found: {entry}")
                    continue
                
                if os.path.isfile(entry):
                    entry = os.sep.join(entry.split(os.sep)[:-1])
                
                if entry not in out:
                    out.append(entry)
        return out

def set_conan_to_waf_os(settings, env):
    #try to map dest os to `waflib.Utils.unversioned_sys_platform()` outputs
    #first, then fallback to just using the conan name directly
    os = settings.get('os', None)
    if os == None:
        return
    if os == 'Macos':
        os = 'darwin'
    elif os == 'Windows':
        os = 'win32'
    else:
        os = os.lower()
    env['DEST_OS'] = os

    version = settings.get('os.version')
    if version:
        env['DEST_OS_VERSION'] = version

    if os == 'win32' and 'os.subsystem' in settings:
        env['WINDOWS_SUBSYSTEM'] = settings['os.subsystem']

    if os == 'android':
        env['ANDROID_MINSDKVERSION'] = settings.get('os.api_level')

    if os in ['ios', 'tvos', 'watchos']:
        env['IOS_SDK_NAME'] = settings.get('os.sdk')
        env['IOS_SDK_MINVER'] = settings.get('os.sdk_version')

def set_conan_to_waf_compiler(settings, env):
    compiler = settings.get('compiler', None)
    if compiler == None:
        return
    libcxx = settings.get('compiler.libcxx')
    runtime = settings.get('compiler.runtime')
    runtime_type = settings.get('compiler.runtime_type')
    threads = settings.get('compiler.threads')
    exception = settings.get('compiler.exception')

    if threads or exception:
        warn(f'WARNING: MinGW flags not handled yet!!')

    env['CXXFLAGS'] = env.get('CXXFLAGS', [])

    #GCC libstd ABI
    if libcxx == 'libstdc++':
        env['CXXFLAGS'].append('-D_GLIBCXX_USE_CXX11_ABI=0')
    elif libcxx == 'libstdc++11':
        env['CXXFLAGS'].append('-D_GLIBCXX_USE_CXX11_ABI=1')

    #Windows CRT
    if runtime and runtime_type:
        flag = 'M' + ('D' if runtime == 'dynamic' else 'T')
        if runtime_type == 'Debug':
            flag += 'd'
        env['CXXFLAGS'].append(f'/{flag}')


def set_conan_to_waf_arch(settings, env):
    #based on Conan settings.yml + `walib.Tools.c_config.MACRO_TO_DEST_CPU`
    #note the original conan arch can be found in the 'CONAN_SETTINGS' key
    arch = settings.get('arch', None)
    if arch == None:
        return
    archmap = {
        'x86_64': [
            'x86_64'
        ],
        'x86': [
            'x86'
        ],
        'mips': [
            'mips',
            'mips64'
        ],
        'sparc': [
            'sparc',
            'sparcv9',
        ],
        'arm':  [
            'armv4',
            'armv4i',
            'armv5el',
            'armv5hf',
            'armv6',
            'armv7',
            'armv7hf',
            'armv7s',
            'armv7k',
            'armv8',
            'armv8_32',
            'armv8.3',
        ],
        'powerpc': [
            'ppc32be',
            'ppc32',
            'ppc64le',
            'ppc64',
        ],
        'sh': [
            'sh4le',
        ],
        's390': [
            's390',
        ],
        's390x': [
            's390x',
        ],
        'xtensa': [
            'xtensalx6',
            'xtensalx106',
            'xtensalx7',
        ],
        'e2k': [
            'e2k-v2',
            'e2k-v3',
            'e2k-v4',
            'e2k-v5',
            'e2k-v6',
            'e2k-v7',
        ],

        #in waf, but not in standard conan settings.yml:
        # '__alpha__'   :'alpha',
        # '__hppa__'    :'hppa',
        # '__convex__'  :'convex',
        # '__m68k__'    :'m68k',

        #in conan, but not in waf
        # avr
        # asm.js
        # wasm
    }
    env['DEST_CPU'] = arch
    for wafname in archmap:
        if arch in archmap[wafname]:
            env['DEST_CPU'] = wafname
            break

waftool_src_template = """# AUTOGENERATED -- DO NOT MODIFY
import os, sys, pathlib
from waflib import Utils
from waflib.Logs import warn
from waflib.Configure import conf
from waflib.Tools.compiler_c import c_compiler
from waflib.Tools.compiler_cxx import cxx_compiler
from waflib.TaskGen import feature, before_method

#---------------------python sys paths from dependencies-----------------------#
# ex: conf.load('some_tool', with_sys_path=True)
%s
#------------------------------------------------------------------------------#

def configure(conf):
    #-------------------configuration info from dependencies-------------------#
    %s
    #--------------------------------------------------------------------------#

    if conf.env.CONAN_BUILDENV:
        import os
        # os.environ.update(conf.env.CONAN_BUILDENV)
        for k, v in conf.env.CONAN_BUILDENV.items():
            os.environ[k] = os.path.expandvars(v)
            conf.environ[k] = os.path.expandvars(v)

    for p in conf.env.ALL_CONAN_PACKAGES:
        conf.msg('Conan usename', p)

    _override_default_compiler_selection(conf, conf.env)
    _apply_cppstd(conf, conf.env)
    _apply_build_type(conf, conf.env)

    conf_info = conf.env.CONAN_CONFIG
    def s(k):
        if not conf.env[k]:
            conf.env[k] = []
        conf.env[k].extend(conf_info[k])
    s('DEFINES')
    s('CFLAGS')
    s('CXXFLAGS')
    s('LINKFLAGS')

@feature("conan")
@before_method("process_use")
def expand_conan_targets(tg):
    uselist = Utils.to_list(getattr(tg, 'use', []))
    for usename in uselist:
        if (f'CONAN_USE_{usename}' in tg.env):
            deps = tg.env[f'CONAN_USE_{usename}']
        else:
            continue
        [uselist.append(r) for r in deps if r not in uselist]
    tg.use = uselist


# helper for installing files from conan packages
#
# def build(bld):
#   bld.install_conan_package(
#       '${PREFIX}',          # install destination
#       use = 'sdl',          # list of conan packages to install
#       recursive = False,    # recursively install deps (default: True)
#       bin = 'binaries',     # install bins to '${PREFIX}/binaries'
#       lib = 'lib',          # (this is a default)
#       include = None,       # set to None to skip install
#       res = None,
#       framework = None
#   )

@conf
def install_conan_package(bld, dest_root, **kw):
    if bld.env.SKIP_INSTALL_CONAN_DEPS or not bld.is_install:
        return

    use = Utils.to_list(kw.get('use'))
    
    dest_bin = kw.get('bin', 'bin')
    dest_lib = kw.get('lib', 'lib')
    dest_res = kw.get('res', 'res')
    dest_include = kw.get('include', 'include')
    dest_framework = kw.get('framework', 'framework')

    bin_out = set()
    lib_out = set()
    res_out = set()
    include_out = set()
    framework_out = set()

    reached = set()
    def _get(name):
        if name in reached:
            return
        reached.add(name)
        if dest_bin:
            bin_out.update(bld.env[f'BINPATH_{name}'])
        if dest_lib:
            lib_out.update(bld.env[f'LIBPATH_{name}'])
        if dest_res:
            res_out.update(bld.env[f'RESPATH_{name}'])
        if dest_include:
            include_out.update(bld.env[f'INCLUDES_{name}'])
        if dest_framework:
            framework_out.update(bld.env[f'FRAMEWORKPATH_{name}'])

        if kw.get('recursive', True):
            dep_uselist = bld.env[f'CONAN_USE_{name}']
            for dep_name in dep_uselist:
                _get(dep_name)

    for name in use:
        _get(name)

    def _install(paths, dest):
        for p in paths:
            if os.path.isabs(p) and os.path.exists(p):
                files = pathlib.Path(p).glob('**/*')
                for file in files:
                    if file.is_dir():
                        continue
                    d = file.relative_to(p)
                    node = bld.root.find_node(str(file))
                    bld.install_as(f'{dest_root}/{dest}/{d}', node)

    _install(bin_out, dest_bin)
    _install(lib_out, dest_lib)
    _install(res_out, dest_res)
    _install(include_out, dest_include)
    _install(framework_out, dest_framework)

def _override_default_compiler_selection(conf, env):
    # The following adds the compiler name to the front of that c_config search
    # list(s). This activates the auto-detection feature for the compiler name.
    # Names are the names of waf tools (see waflib/Tools and waflib/extras for
    # available compilers, e.g. "clangcxx.py")

    # If a compiler isn't supported, they can be configured manually with env
    # variables, like [CC,CXX,AR,etc]. tool_requires packages with compilers can
    # provide this in their `buildenv_info`, or in the [env] section of your
    # build environment's Conan profile while calling `conan install`

    # NOTE: the following does nothing if using env for toolchain selection.

    compile_name_map = {
        #Conan name:    (C++ name, C name)
        'clang':        ('clangxx', 'clang'),
        'apple-clang':  ('clangxx', 'clang'),
        'gcc':          ('gxx', 'gcc'),
        'msvc':         ('msvc', 'msvc'),
        'sun-cc':       ('suncxx', 'suncc'),
        'intel-cc':     ('icpc', 'icc'),
        'qcc':          (None, None),
        'mcst-lcc':     (None, None),
    }
    compiler_name = env.CONAN_SETTINGS['compiler']
    (cxx, cc) = compile_name_map[compiler_name]

    os = Utils.unversioned_sys_platform() # waf uses build os for compiler detection
    if cxx and os in cxx_compiler:
        cxx_compiler[os].insert(0, cxx)
    else:
        assert 0, f"cxx: {cxx}, os: {os}"
    
    if cc and os in c_compiler:
        c_compiler[os].insert(0, cc)

    # MSVC version and targets
    if compiler_name == 'msvc':
        # src: https://blog.knatten.org/2022/08/26/microsoft-c-versions-explained
        # and: https://en.wikipedia.org/wiki/Microsoft_Visual_C++#Internal_version_numbering
        version = str(env.CONAN_SETTINGS['compiler.version'])
        msvc_vermap = {
            '170': 11,
            '180': 12,
            '190': 14,
            '191': 15,
            '192': 16,
            '193': 17,
        }
        arch = env.CONAN_SETTINGS['arch']
        if arch == 'x86_64':
            arch = 'x64'
        elif arch in ['armv4', 'armv4i', 'armv5el', 'armv5hf', 'armv6', 'armv7', 'armv7hf', 'armv7s', 'armv7k']:
            arch = 'arm'
        elif arch.startswith('arm'):
            arch = 'arm64'
        env['MSVC_VERSIONS'] = [f'msvc {msvc_vermap[version]}']
        env['MSVC_TARGETS'] = [arch]

def _apply_cppstd(conf, env):
    cppstd = env.CONAN_SETTINGS.get('compiler.cppstd', None)
    if cppstd == None:
        return

    compiler = env.CONAN_SETTINGS['compiler']

    flags = {
        'gcc': {
            '98':       ['--std', 'c++98'],
            'gnu98':    ['--std', 'gnu++98'],
            '11':       ['--std', 'c++11'],
            'gnu11':    ['--std', 'gnu++11'],
            '14':       ['--std', 'c++14'],
            'gnu14':    ['--std', 'gnu++14'],
            '17':       ['--std', 'c++17'],
            'gnu17':    ['--std', 'gnu++17'],
            '20':       ['--std', 'c++20'],
            'gnu20':    ['--std', 'gnu++20'],
            '23':       ['--std', 'c++23'],
            'gnu23':    ['--std', 'gnu++23'],
        },
        'msvc': {
            '14':       ['/std:c++14'],
            '17':       ['/std:c++17'],
            '20':       ['/std:c++20'],
            '23':       ['/std:latest']
        },
    }
    if compiler not in flags:
        # gcc flags as fallback is probably fine...
        env.append_value('CXXFLAGS', flags['gcc'][cppstd])
    else:
        env.append_value('CXXFLAGS', flags[compiler][cppstd])

def _apply_build_type(conf, env):
    build_type = env.CONAN_SETTINGS.get('build_type', None)
    if build_type == None:
        return

    os = env.CONAN_SETTINGS.get('os', '')
    compiler = env.CONAN_SETTINGS.get('compiler', None)
    if compiler == None:
        _detect_default_waf_compiler_cxx(conf)

    cxxflags = []
    linkflags = []

    if compiler == 'msvc':
        if build_type == 'Debug':
            cxxflags.extend([
                '/Zi',      # generate PDBs
                '/Od',      # disable optimizations
            ])
            linkflags.extend([
                '/debug'
            ])
        elif build_type == 'Release':
            cxxflags.extend([
                '/O2',      # optimize speed
                '/DNDEBUG'
            ])
            linkflags.extend([
                '/incremental:no' # smaller output, functionally equivalent
            ])
        elif build_type == 'RelWithDebInfo':
            cxxflags.extend([
                '/Zi',
                '/O2',
                '/DNDEBUG'
            ])
            linkflags.extend([
                '/debug'
            ])
        elif build_type == 'MinSizeRel':
            cxxflags.extend([
                '/O1',      # optimize size
                '/DNDEBUG'
            ])
            linkflags.extend([
                '/incremental:no'
            ])
    else:
        # Use GCC flags for everything else
        if build_type == 'Debug':
            cxxflags.extend([
                '-g',           # enable debug symbols
                '-O0',          # disable optimizations
            ])
        elif build_type == 'Release':
            cxxflags.extend([
                '-O3',          # optimize speed
                '-DNDEBUG',
            ])
        elif build_type == 'RelWithDebInfo':
            cxxflags.extend([
                '-g',
                '-O2',
                '-DNDEBUG',
            ])
        elif build_type == 'MinSizeRel':
            cxxflags.extend([
                '-Os',          # optimize size
                '-DNDEBUG',
            ])

    env.append_value('CXXFLAGS', cxxflags)
    env.append_value('LINKFLAGS', linkflags)

"""