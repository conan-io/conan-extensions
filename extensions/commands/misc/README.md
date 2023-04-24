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

Output:
<details>

======== Computing dependency graph ========

======== Computing necessary packages ========
bzip2/1.0.8: Forced build from source
gnu-config/cci.20210814: Forced build from source
libffi/3.4.3: Forced build from source
libiconv/1.17: Forced build from source
m4/1.4.19: Forced build from source
ninja/1.11.1: Forced build from source
zlib/1.2.13: Forced build from source
autoconf/2.71: Forced build from source
flex/2.6.4: Forced build from source
libgettext/0.21: Forced build from source
meson/1.0.0: Forced build from source
pcre2/10.42: Forced build from source
bison/3.8.2: Forced build from source
libelf/0.8.13: Forced build from source
pkgconf/1.9.3: Forced build from source
glib/2.76.1: Forced build from source
Requirements
    bzip2/1.0.8#411fc05e80d47a89045edc1ee6f23c1d:0b4c8358bc672fa0c1938091160adbac30ea0114 - Build
    glib/2.76.1#d4b8374c27113a0ef7741b5a1059989c:7e56cb6245d21a98e33c9d818c7fbb7ef5677dc1 - Build
    libelf/0.8.13#2a27c51d562810af629795ac4aa85666:76f7d863f21b130b4e6527af3b1d430f7f8edbea - Build
    libffi/3.4.3#ab23056d668dc13482a811f215f7be3e:76f7d863f21b130b4e6527af3b1d430f7f8edbea - Build
    libgettext/0.21#f4b0a8d73ecaa9f481fe4688b79fb04c:92ceac7f0b5ff565a84e71af76df828d761a3250 - Build
    libiconv/1.17#fa54397801cd96911a8294bc5fc76335:76f7d863f21b130b4e6527af3b1d430f7f8edbea - Build
    pcre2/10.42#2079a0447f9652dffcbbf1eb73ae2d4e:591a43cd410206df1193b783d31bb2bdd42a493f - Build
    zlib/1.2.13#13c96f538b52e1600c40b88994de240f:76f7d863f21b130b4e6527af3b1d430f7f8edbea - Build
Build requirements
    autoconf/2.71#f4e2bd681d49b4b80761aa587bde94d5:da39a3ee5e6b4b0d3255bfef95601890afd80709 - Build
    bison/3.8.2#a8e86b304f8085ddbb22395c99a9a0a8:c8c2c325030311c19e59353a7c57aa8c89fb23c5 - Build
    bzip2/1.0.8#411fc05e80d47a89045edc1ee6f23c1d:0b4c8358bc672fa0c1938091160adbac30ea0114 - Build
    flex/2.6.4#e35bc44b3fcbcd661e0af0dc5b5b1ad4:76f7d863f21b130b4e6527af3b1d430f7f8edbea - Build
    glib/2.76.1#d4b8374c27113a0ef7741b5a1059989c:7e56cb6245d21a98e33c9d818c7fbb7ef5677dc1 - Build
    gnu-config/cci.20210814#15c3bf7dfdb743977b84d0321534ad90:da39a3ee5e6b4b0d3255bfef95601890afd80709 - Build
    libelf/0.8.13#2a27c51d562810af629795ac4aa85666:76f7d863f21b130b4e6527af3b1d430f7f8edbea - Build
    libffi/3.4.3#ab23056d668dc13482a811f215f7be3e:76f7d863f21b130b4e6527af3b1d430f7f8edbea - Build
    libgettext/0.21#f4b0a8d73ecaa9f481fe4688b79fb04c:92ceac7f0b5ff565a84e71af76df828d761a3250 - Build
    libiconv/1.17#fa54397801cd96911a8294bc5fc76335:76f7d863f21b130b4e6527af3b1d430f7f8edbea - Build
    m4/1.4.19#c1c4b1ee919e34630bb9b50046253d3c:617cae191537b47386c088e07b1822d8606b7e67 - Build
    meson/1.0.0#15586c0ac6f682805875ef903dbe7ee2:da39a3ee5e6b4b0d3255bfef95601890afd80709 - Build
    ninja/1.11.1#a2f0b832705907016f336839f96963f8:617cae191537b47386c088e07b1822d8606b7e67 - Build
    pcre2/10.42#2079a0447f9652dffcbbf1eb73ae2d4e:591a43cd410206df1193b783d31bb2bdd42a493f - Build
    pkgconf/1.9.3#a920b5c7f8d04f22b9fe03db91a864dd:df7e47c8f0b96c79c977dd45ec51a050d8380273 - Build
    zlib/1.2.13#13c96f538b52e1600c40b88994de240f:76f7d863f21b130b4e6527af3b1d430f7f8edbea - Build
Adding glib/2.76.1#d4b8374c27113a0ef7741b5a1059989c to download list
Adding libffi/3.4.3#ab23056d668dc13482a811f215f7be3e to download list
Adding pcre2/10.42#2079a0447f9652dffcbbf1eb73ae2d4e to download list
Adding zlib/1.2.13#13c96f538b52e1600c40b88994de240f to download list
Adding bzip2/1.0.8#411fc05e80d47a89045edc1ee6f23c1d to download list
Adding libelf/0.8.13#2a27c51d562810af629795ac4aa85666 to download list
Adding libgettext/0.21#f4b0a8d73ecaa9f481fe4688b79fb04c to download list
Adding libiconv/1.17#fa54397801cd96911a8294bc5fc76335 to download list
Adding meson/1.0.0#15586c0ac6f682805875ef903dbe7ee2 to download list
Adding ninja/1.11.1#a2f0b832705907016f336839f96963f8 to download list
Adding glib/2.76.1#d4b8374c27113a0ef7741b5a1059989c to download list
Adding pkgconf/1.9.3#a920b5c7f8d04f22b9fe03db91a864dd to download list
Adding bison/3.8.2#a8e86b304f8085ddbb22395c99a9a0a8 to download list
Adding flex/2.6.4#e35bc44b3fcbcd661e0af0dc5b5b1ad4 to download list
Adding m4/1.4.19#c1c4b1ee919e34630bb9b50046253d3c to download list
Skip recipe glib/2.76.1#d4b8374c27113a0ef7741b5a1059989c download, already in cache
Skip recipe libffi/3.4.3#ab23056d668dc13482a811f215f7be3e download, already in cache
Skip recipe pcre2/10.42#2079a0447f9652dffcbbf1eb73ae2d4e download, already in cache
Skip recipe zlib/1.2.13#13c96f538b52e1600c40b88994de240f download, already in cache
Skip recipe bzip2/1.0.8#411fc05e80d47a89045edc1ee6f23c1d download, already in cache
Skip recipe libelf/0.8.13#2a27c51d562810af629795ac4aa85666 download, already in cache
Skip recipe libgettext/0.21#f4b0a8d73ecaa9f481fe4688b79fb04c download, already in cache
Skip recipe libiconv/1.17#fa54397801cd96911a8294bc5fc76335 download, already in cache
Skip recipe meson/1.0.0#15586c0ac6f682805875ef903dbe7ee2 download, already in cache
Skip recipe ninja/1.11.1#a2f0b832705907016f336839f96963f8 download, already in cache
Skip recipe pkgconf/1.9.3#a920b5c7f8d04f22b9fe03db91a864dd download, already in cache
Skip recipe bison/3.8.2#a8e86b304f8085ddbb22395c99a9a0a8 download, already in cache
Skip recipe flex/2.6.4#e35bc44b3fcbcd661e0af0dc5b5b1ad4 download, already in cache
Skip recipe m4/1.4.19#c1c4b1ee919e34630bb9b50046253d3c download, already in cache
Skip package glib/2.76.1#d4b8374c27113a0ef7741b5a1059989c:237027f68dbdf9bc451dd138d5baf1733f26cb21#107df8d4bc6e06f36009e7e37e9d026b download, already in cache
Skip package glib/2.76.1#d4b8374c27113a0ef7741b5a1059989c:755391e6179a19b5ea100ab20f6a09cf0532b245#e8ff2c6d8a2add716c5d02d2b6090ee9 download, already in cache
Skip package glib/2.76.1#d4b8374c27113a0ef7741b5a1059989c:8b9ffae61fce27bad3e579843eea6d2b0aaf36dc#d265385fef1625fc8e603215cbc241e4 download, already in cache
Skip package glib/2.76.1#d4b8374c27113a0ef7741b5a1059989c:8cc19df09a1ca483960d2e460156391f43ae6ee8#89b0ca1fa10aed4a36e59a56eff16ce1 download, already in cache
Skip package glib/2.76.1#d4b8374c27113a0ef7741b5a1059989c:9c8f81fd83d455eba12c3f56b85563a57d60a7fe#fcb183f69127254d89f6b981da4d08d0 download, already in cache
Skip package glib/2.76.1#d4b8374c27113a0ef7741b5a1059989c:bdd5d4b3f8260cb32667aed537d3361c3ecb6c9a#e165eb3836585e4f9f8e52cad9416eab download, already in cache
Skip package glib/2.76.1#d4b8374c27113a0ef7741b5a1059989c:f308f34ee05e34564ff9ffd65e0ba48d6c5b1149#53d29150d6acc405e7c6c919c75e91a8 download, already in cache
Skip package libffi/3.4.3#ab23056d668dc13482a811f215f7be3e:24612164eb0760405fcd237df0102e554ed1cb2f#3e59477afb6644382d178e232c32f6c3 download, already in cache
Skip package libffi/3.4.3#ab23056d668dc13482a811f215f7be3e:41ad450120fdab2266b1185a967d298f7ae52595#703dd27cde1d803eac6a045eccb80881 download, already in cache
Skip package libffi/3.4.3#ab23056d668dc13482a811f215f7be3e:76864d438e6a53828b8769476a7b57a241d91b69#659e77400f4b93b964573d173e900e9f download, already in cache
Skip package libffi/3.4.3#ab23056d668dc13482a811f215f7be3e:a3c9d80d887539fac38b81ff8cd4585fe42027e0#39075221d0fb6dddf762362b0df4d4e8 download, already in cache
Skip package libffi/3.4.3#ab23056d668dc13482a811f215f7be3e:abe5e2b04ea92ce2ee91bc9834317dbe66628206#3fcfe32607f958861f7f5d9e02a8e1d4 download, already in cache
Skip package libffi/3.4.3#ab23056d668dc13482a811f215f7be3e:ae9eaf478e918e6470fe64a4d8d4d9552b0b3606#988b05c80f6aa89be687fca86351dad2 download, already in cache
Skip package libffi/3.4.3#ab23056d668dc13482a811f215f7be3e:b647c43bfefae3f830561ca202b6cfd935b56205#939bc38872a6de216adafe8ac0b97e36 download, already in cache
Skip package libffi/3.4.3#ab23056d668dc13482a811f215f7be3e:d62dff20d86436b9c58ddc0162499d197be9de1e#2007d4d3e5a3f6bbb3cd582d6aa04fb1 download, already in cache
Skip package libffi/3.4.3#ab23056d668dc13482a811f215f7be3e:dbb40f41e6e9a5c4a9a1fd8d9e6ccf6d92676c92#3d6e6e79b7e4c74ec110b78763d242a0 download, already in cache
Skip package pcre2/10.42#2079a0447f9652dffcbbf1eb73ae2d4e:0cc5d1048b29a3d42f5b50fb6075049c5d29e191#2b8b14a1c4002c971314c04bf4a8c66c download, already in cache
Skip package pcre2/10.42#2079a0447f9652dffcbbf1eb73ae2d4e:5f5ae52ee464408b06364f3002226ecdc97efa7b#9e1bf3c2bc00c837fce06f6c76483b9b download, already in cache
Skip package pcre2/10.42#2079a0447f9652dffcbbf1eb73ae2d4e:63a9023dfe81d69c11ec4255b6926bd4ecbc3bf9#ec32787e5d0270d20055c9f10e3a5fc7 download, already in cache
Skip package pcre2/10.42#2079a0447f9652dffcbbf1eb73ae2d4e:8d0721e12496b6316bae8bfbb2be21c784190a36#4fa768a65fd20652af7061ddac70f679 download, already in cache
Skip package pcre2/10.42#2079a0447f9652dffcbbf1eb73ae2d4e:8db53c500ccbb080344f64e60f680c0245dc769d#b64ed26c4f110af6a2816d92b9760e77 download, already in cache
Skip package pcre2/10.42#2079a0447f9652dffcbbf1eb73ae2d4e:8f6c1c12c8eb795028c6d7912d086d4367d24cfc#c9022e410ab6e7cee50ed51ef48cd925 download, already in cache
Skip package pcre2/10.42#2079a0447f9652dffcbbf1eb73ae2d4e:95a990d9d9e0bfa380e780b20b0fca17b72b2e71#2d904de99a4c0bc4f35515a9bd548bef download, already in cache
Skip package pcre2/10.42#2079a0447f9652dffcbbf1eb73ae2d4e:ac6c828b099b511ea9c70b470fa71ca3a9df33cb#ddd1587f10b5f24bc14fa44650081404 download, already in cache
Skip package pcre2/10.42#2079a0447f9652dffcbbf1eb73ae2d4e:dec24e389821756f046850665ac2dc2e4fb7634e#64f895bdde4679765feed0e494deb7f7 download, already in cache
Skip package zlib/1.2.13#13c96f538b52e1600c40b88994de240f:24612164eb0760405fcd237df0102e554ed1cb2f#8b6a5d9c2a3818363724ebe499636396 download, already in cache
Skip package zlib/1.2.13#13c96f538b52e1600c40b88994de240f:41ad450120fdab2266b1185a967d298f7ae52595#6db1a955495ed79c7834d10a710a9882 download, already in cache
Skip package zlib/1.2.13#13c96f538b52e1600c40b88994de240f:76864d438e6a53828b8769476a7b57a241d91b69#0daf13fb50d1a37d725419914af3a33e download, already in cache
Skip package zlib/1.2.13#13c96f538b52e1600c40b88994de240f:a3c9d80d887539fac38b81ff8cd4585fe42027e0#71f1ffe74c50b8d984818922644fd3f2 download, already in cache
Skip package zlib/1.2.13#13c96f538b52e1600c40b88994de240f:abe5e2b04ea92ce2ee91bc9834317dbe66628206#441a647ceea3b33b1b0dbe1bef7a807d download, already in cache
Skip package zlib/1.2.13#13c96f538b52e1600c40b88994de240f:ae9eaf478e918e6470fe64a4d8d4d9552b0b3606#0255fcf347dc3906fe9a1e471caaf387 download, already in cache
Skip package zlib/1.2.13#13c96f538b52e1600c40b88994de240f:b647c43bfefae3f830561ca202b6cfd935b56205#2e32f26e1daeb405642fe7824a3f333c download, already in cache
Skip package zlib/1.2.13#13c96f538b52e1600c40b88994de240f:d62dff20d86436b9c58ddc0162499d197be9de1e#4f5015205193284adb6621ed40e04fbb download, already in cache
Skip package zlib/1.2.13#13c96f538b52e1600c40b88994de240f:dbb40f41e6e9a5c4a9a1fd8d9e6ccf6d92676c92#2a94864edad57638965c20938af607af download, already in cache
Skip package bzip2/1.0.8#411fc05e80d47a89045edc1ee6f23c1d:12b38c622ab94fbabd118653840a0f5f7c93b72d#a95126de789be8bebf59163c8b445fab download, already in cache
Skip package bzip2/1.0.8#411fc05e80d47a89045edc1ee6f23c1d:4727ab30388835e9b1e1c9b0d16636a9d64e7d0d#015fb37a2e668503c2bfd5e28c9bcb73 download, already in cache
Skip package bzip2/1.0.8#411fc05e80d47a89045edc1ee6f23c1d:582795513620c02434315fe471662206b3a90c44#b812d992549c98cd781d28fb30f67c84 download, already in cache
Skip package bzip2/1.0.8#411fc05e80d47a89045edc1ee6f23c1d:68ee460482c7172b8510a83e90b58ca3f3a67084#32a194eb95b0959e413fe790969e32a4 download, already in cache
Skip package bzip2/1.0.8#411fc05e80d47a89045edc1ee6f23c1d:763ddd53d7a4775fe84a285f56005a096d9786fd#3c39f4d84b7d234e9632c57059cc49f5 download, already in cache
Skip package bzip2/1.0.8#411fc05e80d47a89045edc1ee6f23c1d:7645c72fda51c031fb76bfa52ec668575e91e8e3#d98e9a167c4fab710dc27cd25e65d819 download, already in cache
Skip package bzip2/1.0.8#411fc05e80d47a89045edc1ee6f23c1d:7fd8d46eaa8d8c5b8af6db2d900fdd898c3bf460#f7e9db7e8f992d9542219b1d53aa0254 download, already in cache
Skip package bzip2/1.0.8#411fc05e80d47a89045edc1ee6f23c1d:a8fb9158e8f911ce0e9a69916033d3c06f6abea5#781ce86accb876682ac1e22fc15ec1b4 download, already in cache
Skip package bzip2/1.0.8#411fc05e80d47a89045edc1ee6f23c1d:e3dc948df7773c2c60edf3a72557250108721b20#85dde2c7b77278a20fec3d59f9fbeb3b download, already in cache
Skip package libelf/0.8.13#2a27c51d562810af629795ac4aa85666:41ad450120fdab2266b1185a967d298f7ae52595#ff410122b150f83283ec1231726059e1 download, already in cache
Skip package libelf/0.8.13#2a27c51d562810af629795ac4aa85666:76864d438e6a53828b8769476a7b57a241d91b69#befc20aca19456e63d0c632612d64703 download, already in cache
Skip package libelf/0.8.13#2a27c51d562810af629795ac4aa85666:abe5e2b04ea92ce2ee91bc9834317dbe66628206#4132a17033da50fd053b37f478c5cbfa download, already in cache
Skip package libelf/0.8.13#2a27c51d562810af629795ac4aa85666:ae9eaf478e918e6470fe64a4d8d4d9552b0b3606#0ad46515b823c661e743bf316ae41004 download, already in cache
Skip package libelf/0.8.13#2a27c51d562810af629795ac4aa85666:b647c43bfefae3f830561ca202b6cfd935b56205#742c7372907e824afcb7c8a9e38782b5 download, already in cache
Skip package libelf/0.8.13#2a27c51d562810af629795ac4aa85666:d62dff20d86436b9c58ddc0162499d197be9de1e#df17da1997f9f23d360e17cdfacc4571 download, already in cache
Skip package libelf/0.8.13#2a27c51d562810af629795ac4aa85666:dbb40f41e6e9a5c4a9a1fd8d9e6ccf6d92676c92#d54cf6d6b13a06fce3cc7f13c9d94954 download, already in cache
Skip package libgettext/0.21#f4b0a8d73ecaa9f481fe4688b79fb04c:044c50aa099b6d33921301fa78acd938853d68d1#6244684cc06c89eb326d7d0d1d74d1a0 download, already in cache
Skip package libgettext/0.21#f4b0a8d73ecaa9f481fe4688b79fb04c:05dfcf8238ea0a7d5549bc855931f22f47c9a9d4#d0c2ecdacb35eafe5d25f160269df00a download, already in cache
Skip package libgettext/0.21#f4b0a8d73ecaa9f481fe4688b79fb04c:0c165c8264558c0163a68076c73a35d722a5157c#fcc6613164f7a88123fde713b078b668 download, already in cache
Skip package libgettext/0.21#f4b0a8d73ecaa9f481fe4688b79fb04c:0c32fad799e8746f66aba9802e5d79ebcff3fada#67a9e9ad6469f7a136716cf907bfe9fc download, already in cache
Skip package libgettext/0.21#f4b0a8d73ecaa9f481fe4688b79fb04c:4fdcdcec781b3aa9d725a1acafacc666a2729855#47b8a75f7b70e87d7f78f8277bb9f198 download, already in cache
Skip package libgettext/0.21#f4b0a8d73ecaa9f481fe4688b79fb04c:68474ea6a6026ad3ad74f81c5a8eb0873000e2d3#641961b4a1bcb3a350241e284b14d701 download, already in cache
Skip package libgettext/0.21#f4b0a8d73ecaa9f481fe4688b79fb04c:7bf9db7f4a1fb3f029a1a9b30d0258c77a213b46#d44c81125b8bba05e075ed5fecfee225 download, already in cache
Skip package libgettext/0.21#f4b0a8d73ecaa9f481fe4688b79fb04c:a609e78c43d7b7921f58f508987352079046d225#c77ccc1e9445d87ff005a1d015103529 download, already in cache
Skip package libgettext/0.21#f4b0a8d73ecaa9f481fe4688b79fb04c:c95b4dde874d2aadec0d5cc95d188b1b115f4ed0#951d012d314ac3f68dd09bede85d8806 download, already in cache
Skip package libiconv/1.17#fa54397801cd96911a8294bc5fc76335:24612164eb0760405fcd237df0102e554ed1cb2f#26e37a4e9f9ded024a33a66863e74d6b download, already in cache
Skip package libiconv/1.17#fa54397801cd96911a8294bc5fc76335:41ad450120fdab2266b1185a967d298f7ae52595#cf7c954738a4a81fd68bf7671465b350 download, already in cache
Skip package libiconv/1.17#fa54397801cd96911a8294bc5fc76335:76864d438e6a53828b8769476a7b57a241d91b69#75ffc5d59aea5a9fc7b41e07d4265f37 download, already in cache
Skip package libiconv/1.17#fa54397801cd96911a8294bc5fc76335:a3c9d80d887539fac38b81ff8cd4585fe42027e0#23ff9eb9a19f9ec623af4c81fb1b717a download, already in cache
Skip package libiconv/1.17#fa54397801cd96911a8294bc5fc76335:abe5e2b04ea92ce2ee91bc9834317dbe66628206#3cbb797095f66828f6f09d715f77cb71 download, already in cache
Skip package libiconv/1.17#fa54397801cd96911a8294bc5fc76335:ae9eaf478e918e6470fe64a4d8d4d9552b0b3606#669ec67f5e2341df39e0389e12421e77 download, already in cache
Skip package libiconv/1.17#fa54397801cd96911a8294bc5fc76335:b647c43bfefae3f830561ca202b6cfd935b56205#fb0673713e76a055437cd2d225556268 download, already in cache
Skip package libiconv/1.17#fa54397801cd96911a8294bc5fc76335:d62dff20d86436b9c58ddc0162499d197be9de1e#c230e582baef26b39e7451d02b5a5f7a download, already in cache
Skip package libiconv/1.17#fa54397801cd96911a8294bc5fc76335:dbb40f41e6e9a5c4a9a1fd8d9e6ccf6d92676c92#ba60c975bbf6ff7c6b93551e264c8927 download, already in cache
Skip package meson/1.0.0#15586c0ac6f682805875ef903dbe7ee2:da39a3ee5e6b4b0d3255bfef95601890afd80709#5c8fd51fc33f12e26519674d99afd0e5 download, already in cache
Skip package ninja/1.11.1#a2f0b832705907016f336839f96963f8:3593751651824fb813502c69c971267624ced41a#a53f170b60a46aef75ead8658bdeae05 download, already in cache
Skip package ninja/1.11.1#a2f0b832705907016f336839f96963f8:617cae191537b47386c088e07b1822d8606b7e67#c91372a33f74405b60f9f71b2163a290 download, already in cache
Skip package ninja/1.11.1#a2f0b832705907016f336839f96963f8:723257509aee8a72faf021920c2874abc738e029#2af209f6b38a9f7b2c777c6bff456ffb download, already in cache
Skip package ninja/1.11.1#a2f0b832705907016f336839f96963f8:9ac8640923e5284645f8852ef8ba335654f4020e#0943503a21a3beb1238c0805dacc4d28 download, already in cache
Skip package pkgconf/1.9.3#a920b5c7f8d04f22b9fe03db91a864dd:43771b8671ac44479c188dd72670e2eb2d7918a6#ce4d1d61f0b05d4229631aa740250685 download, already in cache
Skip package pkgconf/1.9.3#a920b5c7f8d04f22b9fe03db91a864dd:8b5cf1367c351fd3c60ef4e28c1a50612761b13e#4ee5b12713113deadea85ed447d0e655 download, already in cache
Skip package pkgconf/1.9.3#a920b5c7f8d04f22b9fe03db91a864dd:c0b621fd4b3199fe05075171573398833dba85f4#a231c33e360d8be4e90467b36b88f027 download, already in cache
Skip package pkgconf/1.9.3#a920b5c7f8d04f22b9fe03db91a864dd:df7e47c8f0b96c79c977dd45ec51a050d8380273#ffb7995c86a762b52da14de294154467 download, already in cache
Skip package bison/3.8.2#a8e86b304f8085ddbb22395c99a9a0a8:500c2a3f502e0ca7d4a4c65cb2a4a0b0a24994f5#6e426a4fff8e364779169ab986a1daa3 download, already in cache
Skip package bison/3.8.2#a8e86b304f8085ddbb22395c99a9a0a8:812844a246c05915dcfd8c471dbf04d2834dc0f9#b4ebb174a7c42d14419c51aa2be4480b download, already in cache
Skip package bison/3.8.2#a8e86b304f8085ddbb22395c99a9a0a8:9a523dd17a4da54882f7a1e363b21c4a141d314f#bf48544cf6e5037d1ed00c25a480c575 download, already in cache
Skip package flex/2.6.4#e35bc44b3fcbcd661e0af0dc5b5b1ad4:24612164eb0760405fcd237df0102e554ed1cb2f#324afa01f05f7e37fdbdc931357db407 download, already in cache
Skip package flex/2.6.4#e35bc44b3fcbcd661e0af0dc5b5b1ad4:a3c9d80d887539fac38b81ff8cd4585fe42027e0#2ea834019a3a03dbaac1be5023e55ce6 download, already in cache
Skip package flex/2.6.4#e35bc44b3fcbcd661e0af0dc5b5b1ad4:abe5e2b04ea92ce2ee91bc9834317dbe66628206#7602a676ca6bca378805ca1847eb617c download, already in cache
Skip package flex/2.6.4#e35bc44b3fcbcd661e0af0dc5b5b1ad4:b647c43bfefae3f830561ca202b6cfd935b56205#d18545ed84d684e0090595f1eb0d23c5 download, already in cache
Skip package flex/2.6.4#e35bc44b3fcbcd661e0af0dc5b5b1ad4:d62dff20d86436b9c58ddc0162499d197be9de1e#f9fa036bc05554a2c016d6f42a27dc7b download, already in cache
Skip package flex/2.6.4#e35bc44b3fcbcd661e0af0dc5b5b1ad4:dbb40f41e6e9a5c4a9a1fd8d9e6ccf6d92676c92#8acda13cf8bf1f468de27db65531fedf download, already in cache
Skip package m4/1.4.19#c1c4b1ee919e34630bb9b50046253d3c:3593751651824fb813502c69c971267624ced41a#c69dc2230d016a77b5514d9916b14714 download, already in cache
Skip package m4/1.4.19#c1c4b1ee919e34630bb9b50046253d3c:617cae191537b47386c088e07b1822d8606b7e67#af3bb664b82c4f616d3146625c5b4bd5 download, already in cache
Skip package m4/1.4.19#c1c4b1ee919e34630bb9b50046253d3c:723257509aee8a72faf021920c2874abc738e029#0b5e50355c3e4e4e9e3434f96167ed09 download, already in cache
Skip package m4/1.4.19#c1c4b1ee919e34630bb9b50046253d3c:9ac8640923e5284645f8852ef8ba335654f4020e#0b930e2019f5dfbf0c5e4ed8b8be9bf1 download, already in cache
Checking which revisions exist in the remote server
Recipe 'glib/2.76.1#d4b8374c27113a0ef7741b5a1059989c' already in server, skipping upload
Package 'glib/2.76.1#d4b8374c27113a0ef7741b5a1059989c:237027f68dbdf9bc451dd138d5baf1733f26cb21#107df8d4bc6e06f36009e7e37e9d026b' already in server, skipping upload
Package 'glib/2.76.1#d4b8374c27113a0ef7741b5a1059989c:755391e6179a19b5ea100ab20f6a09cf0532b245#e8ff2c6d8a2add716c5d02d2b6090ee9' already in server, skipping upload
Package 'glib/2.76.1#d4b8374c27113a0ef7741b5a1059989c:8b9ffae61fce27bad3e579843eea6d2b0aaf36dc#d265385fef1625fc8e603215cbc241e4' already in server, skipping upload
Package 'glib/2.76.1#d4b8374c27113a0ef7741b5a1059989c:8cc19df09a1ca483960d2e460156391f43ae6ee8#89b0ca1fa10aed4a36e59a56eff16ce1' already in server, skipping upload
Package 'glib/2.76.1#d4b8374c27113a0ef7741b5a1059989c:9c8f81fd83d455eba12c3f56b85563a57d60a7fe#fcb183f69127254d89f6b981da4d08d0' already in server, skipping upload
Package 'glib/2.76.1#d4b8374c27113a0ef7741b5a1059989c:bdd5d4b3f8260cb32667aed537d3361c3ecb6c9a#e165eb3836585e4f9f8e52cad9416eab' already in server, skipping upload
Package 'glib/2.76.1#d4b8374c27113a0ef7741b5a1059989c:f308f34ee05e34564ff9ffd65e0ba48d6c5b1149#53d29150d6acc405e7c6c919c75e91a8' already in server, skipping upload
Checking which revisions exist in the remote server
Checking which revisions exist in the remote server
Checking which revisions exist in the remote server
Recipe 'zlib/1.2.13#13c96f538b52e1600c40b88994de240f' already in server, skipping upload
Package 'zlib/1.2.13#13c96f538b52e1600c40b88994de240f:24612164eb0760405fcd237df0102e554ed1cb2f#8b6a5d9c2a3818363724ebe499636396' already in server, skipping upload
Package 'zlib/1.2.13#13c96f538b52e1600c40b88994de240f:41ad450120fdab2266b1185a967d298f7ae52595#6db1a955495ed79c7834d10a710a9882' already in server, skipping upload
Package 'zlib/1.2.13#13c96f538b52e1600c40b88994de240f:76864d438e6a53828b8769476a7b57a241d91b69#0daf13fb50d1a37d725419914af3a33e' already in server, skipping upload
Package 'zlib/1.2.13#13c96f538b52e1600c40b88994de240f:a3c9d80d887539fac38b81ff8cd4585fe42027e0#71f1ffe74c50b8d984818922644fd3f2' already in server, skipping upload
Package 'zlib/1.2.13#13c96f538b52e1600c40b88994de240f:abe5e2b04ea92ce2ee91bc9834317dbe66628206#441a647ceea3b33b1b0dbe1bef7a807d' already in server, skipping upload
Package 'zlib/1.2.13#13c96f538b52e1600c40b88994de240f:ae9eaf478e918e6470fe64a4d8d4d9552b0b3606#0255fcf347dc3906fe9a1e471caaf387' already in server, skipping upload
Package 'zlib/1.2.13#13c96f538b52e1600c40b88994de240f:b647c43bfefae3f830561ca202b6cfd935b56205#2e32f26e1daeb405642fe7824a3f333c' already in server, skipping upload
Package 'zlib/1.2.13#13c96f538b52e1600c40b88994de240f:d62dff20d86436b9c58ddc0162499d197be9de1e#4f5015205193284adb6621ed40e04fbb' already in server, skipping upload
Package 'zlib/1.2.13#13c96f538b52e1600c40b88994de240f:dbb40f41e6e9a5c4a9a1fd8d9e6ccf6d92676c92#2a94864edad57638965c20938af607af' already in server, skipping upload
Checking which revisions exist in the remote server
Checking which revisions exist in the remote server
Checking which revisions exist in the remote server
Checking which revisions exist in the remote server
Checking which revisions exist in the remote server
Checking which revisions exist in the remote server
Checking which revisions exist in the remote server
Checking which revisions exist in the remote server
Checking which revisions exist in the remote server
Checking which revisions exist in the remote server
Preparing artifacts to upload
Decompressing conan_sources.tgz
Sources downloaded from 'conancenter'
Sources downloaded from 'conancenter'
Decompressing conan_sources.tgz
Sources downloaded from 'conancenter'
Decompressing conan_sources.tgz
Sources downloaded from 'conancenter'
Decompressing conan_sources.tgz
Sources downloaded from 'conancenter'
Sources downloaded from 'conancenter'
Decompressing conan_sources.tgz
Sources downloaded from 'conancenter'
Decompressing conan_sources.tgz
Sources downloaded from 'conancenter'
Decompressing conan_sources.tgz
Sources downloaded from 'conancenter'
Decompressing conan_sources.tgz
Sources downloaded from 'conancenter'
Uploading artifacts
Uploading recipe 'libffi/3.4.3#ab23056d668dc13482a811f215f7be3e'
Uploading package 'libffi/3.4.3#ab23056d668dc13482a811f215f7be3e:24612164eb0760405fcd237df0102e554ed1cb2f#3e59477afb6644382d178e232c32f6c3'
Uploading package 'libffi/3.4.3#ab23056d668dc13482a811f215f7be3e:41ad450120fdab2266b1185a967d298f7ae52595#703dd27cde1d803eac6a045eccb80881'
Uploading package 'libffi/3.4.3#ab23056d668dc13482a811f215f7be3e:76864d438e6a53828b8769476a7b57a241d91b69#659e77400f4b93b964573d173e900e9f'
Uploading package 'libffi/3.4.3#ab23056d668dc13482a811f215f7be3e:a3c9d80d887539fac38b81ff8cd4585fe42027e0#39075221d0fb6dddf762362b0df4d4e8'
Uploading package 'libffi/3.4.3#ab23056d668dc13482a811f215f7be3e:abe5e2b04ea92ce2ee91bc9834317dbe66628206#3fcfe32607f958861f7f5d9e02a8e1d4'
Uploading package 'libffi/3.4.3#ab23056d668dc13482a811f215f7be3e:ae9eaf478e918e6470fe64a4d8d4d9552b0b3606#988b05c80f6aa89be687fca86351dad2'
Uploading package 'libffi/3.4.3#ab23056d668dc13482a811f215f7be3e:b647c43bfefae3f830561ca202b6cfd935b56205#939bc38872a6de216adafe8ac0b97e36'
Uploading package 'libffi/3.4.3#ab23056d668dc13482a811f215f7be3e:d62dff20d86436b9c58ddc0162499d197be9de1e#2007d4d3e5a3f6bbb3cd582d6aa04fb1'
Uploading package 'libffi/3.4.3#ab23056d668dc13482a811f215f7be3e:dbb40f41e6e9a5c4a9a1fd8d9e6ccf6d92676c92#3d6e6e79b7e4c74ec110b78763d242a0'
Uploading recipe 'pcre2/10.42#2079a0447f9652dffcbbf1eb73ae2d4e'
Uploading package 'pcre2/10.42#2079a0447f9652dffcbbf1eb73ae2d4e:0cc5d1048b29a3d42f5b50fb6075049c5d29e191#2b8b14a1c4002c971314c04bf4a8c66c'
Uploading package 'pcre2/10.42#2079a0447f9652dffcbbf1eb73ae2d4e:5f5ae52ee464408b06364f3002226ecdc97efa7b#9e1bf3c2bc00c837fce06f6c76483b9b'
Uploading package 'pcre2/10.42#2079a0447f9652dffcbbf1eb73ae2d4e:63a9023dfe81d69c11ec4255b6926bd4ecbc3bf9#ec32787e5d0270d20055c9f10e3a5fc7'
Uploading package 'pcre2/10.42#2079a0447f9652dffcbbf1eb73ae2d4e:8d0721e12496b6316bae8bfbb2be21c784190a36#4fa768a65fd20652af7061ddac70f679'
Uploading package 'pcre2/10.42#2079a0447f9652dffcbbf1eb73ae2d4e:8db53c500ccbb080344f64e60f680c0245dc769d#b64ed26c4f110af6a2816d92b9760e77'
Uploading package 'pcre2/10.42#2079a0447f9652dffcbbf1eb73ae2d4e:8f6c1c12c8eb795028c6d7912d086d4367d24cfc#c9022e410ab6e7cee50ed51ef48cd925'
Uploading package 'pcre2/10.42#2079a0447f9652dffcbbf1eb73ae2d4e:95a990d9d9e0bfa380e780b20b0fca17b72b2e71#2d904de99a4c0bc4f35515a9bd548bef'
Uploading package 'pcre2/10.42#2079a0447f9652dffcbbf1eb73ae2d4e:ac6c828b099b511ea9c70b470fa71ca3a9df33cb#ddd1587f10b5f24bc14fa44650081404'
Uploading package 'pcre2/10.42#2079a0447f9652dffcbbf1eb73ae2d4e:dec24e389821756f046850665ac2dc2e4fb7634e#64f895bdde4679765feed0e494deb7f7'
Uploading recipe 'bzip2/1.0.8#411fc05e80d47a89045edc1ee6f23c1d'
Uploading package 'bzip2/1.0.8#411fc05e80d47a89045edc1ee6f23c1d:12b38c622ab94fbabd118653840a0f5f7c93b72d#a95126de789be8bebf59163c8b445fab'
Uploading package 'bzip2/1.0.8#411fc05e80d47a89045edc1ee6f23c1d:4727ab30388835e9b1e1c9b0d16636a9d64e7d0d#015fb37a2e668503c2bfd5e28c9bcb73'
Uploading package 'bzip2/1.0.8#411fc05e80d47a89045edc1ee6f23c1d:582795513620c02434315fe471662206b3a90c44#b812d992549c98cd781d28fb30f67c84'
Uploading package 'bzip2/1.0.8#411fc05e80d47a89045edc1ee6f23c1d:68ee460482c7172b8510a83e90b58ca3f3a67084#32a194eb95b0959e413fe790969e32a4'
Uploading package 'bzip2/1.0.8#411fc05e80d47a89045edc1ee6f23c1d:763ddd53d7a4775fe84a285f56005a096d9786fd#3c39f4d84b7d234e9632c57059cc49f5'
Uploading package 'bzip2/1.0.8#411fc05e80d47a89045edc1ee6f23c1d:7645c72fda51c031fb76bfa52ec668575e91e8e3#d98e9a167c4fab710dc27cd25e65d819'
Uploading package 'bzip2/1.0.8#411fc05e80d47a89045edc1ee6f23c1d:7fd8d46eaa8d8c5b8af6db2d900fdd898c3bf460#f7e9db7e8f992d9542219b1d53aa0254'
Uploading package 'bzip2/1.0.8#411fc05e80d47a89045edc1ee6f23c1d:a8fb9158e8f911ce0e9a69916033d3c06f6abea5#781ce86accb876682ac1e22fc15ec1b4'
Uploading package 'bzip2/1.0.8#411fc05e80d47a89045edc1ee6f23c1d:e3dc948df7773c2c60edf3a72557250108721b20#85dde2c7b77278a20fec3d59f9fbeb3b'
Uploading recipe 'libelf/0.8.13#2a27c51d562810af629795ac4aa85666'
Uploading package 'libelf/0.8.13#2a27c51d562810af629795ac4aa85666:41ad450120fdab2266b1185a967d298f7ae52595#ff410122b150f83283ec1231726059e1'
Uploading package 'libelf/0.8.13#2a27c51d562810af629795ac4aa85666:76864d438e6a53828b8769476a7b57a241d91b69#befc20aca19456e63d0c632612d64703'
Uploading package 'libelf/0.8.13#2a27c51d562810af629795ac4aa85666:abe5e2b04ea92ce2ee91bc9834317dbe66628206#4132a17033da50fd053b37f478c5cbfa'
Uploading package 'libelf/0.8.13#2a27c51d562810af629795ac4aa85666:ae9eaf478e918e6470fe64a4d8d4d9552b0b3606#0ad46515b823c661e743bf316ae41004'
Uploading package 'libelf/0.8.13#2a27c51d562810af629795ac4aa85666:b647c43bfefae3f830561ca202b6cfd935b56205#742c7372907e824afcb7c8a9e38782b5'
Uploading package 'libelf/0.8.13#2a27c51d562810af629795ac4aa85666:d62dff20d86436b9c58ddc0162499d197be9de1e#df17da1997f9f23d360e17cdfacc4571'
Uploading package 'libelf/0.8.13#2a27c51d562810af629795ac4aa85666:dbb40f41e6e9a5c4a9a1fd8d9e6ccf6d92676c92#d54cf6d6b13a06fce3cc7f13c9d94954'
Uploading recipe 'libgettext/0.21#f4b0a8d73ecaa9f481fe4688b79fb04c'
Uploading package 'libgettext/0.21#f4b0a8d73ecaa9f481fe4688b79fb04c:044c50aa099b6d33921301fa78acd938853d68d1#6244684cc06c89eb326d7d0d1d74d1a0'
Uploading package 'libgettext/0.21#f4b0a8d73ecaa9f481fe4688b79fb04c:05dfcf8238ea0a7d5549bc855931f22f47c9a9d4#d0c2ecdacb35eafe5d25f160269df00a'
Uploading package 'libgettext/0.21#f4b0a8d73ecaa9f481fe4688b79fb04c:0c165c8264558c0163a68076c73a35d722a5157c#fcc6613164f7a88123fde713b078b668'
Uploading package 'libgettext/0.21#f4b0a8d73ecaa9f481fe4688b79fb04c:0c32fad799e8746f66aba9802e5d79ebcff3fada#67a9e9ad6469f7a136716cf907bfe9fc'
Uploading package 'libgettext/0.21#f4b0a8d73ecaa9f481fe4688b79fb04c:4fdcdcec781b3aa9d725a1acafacc666a2729855#47b8a75f7b70e87d7f78f8277bb9f198'
Uploading package 'libgettext/0.21#f4b0a8d73ecaa9f481fe4688b79fb04c:68474ea6a6026ad3ad74f81c5a8eb0873000e2d3#641961b4a1bcb3a350241e284b14d701'
Uploading package 'libgettext/0.21#f4b0a8d73ecaa9f481fe4688b79fb04c:7bf9db7f4a1fb3f029a1a9b30d0258c77a213b46#d44c81125b8bba05e075ed5fecfee225'
Uploading package 'libgettext/0.21#f4b0a8d73ecaa9f481fe4688b79fb04c:a609e78c43d7b7921f58f508987352079046d225#c77ccc1e9445d87ff005a1d015103529'
Uploading package 'libgettext/0.21#f4b0a8d73ecaa9f481fe4688b79fb04c:c95b4dde874d2aadec0d5cc95d188b1b115f4ed0#951d012d314ac3f68dd09bede85d8806'
Uploading recipe 'libiconv/1.17#fa54397801cd96911a8294bc5fc76335'
Uploading package 'libiconv/1.17#fa54397801cd96911a8294bc5fc76335:24612164eb0760405fcd237df0102e554ed1cb2f#26e37a4e9f9ded024a33a66863e74d6b'
Uploading package 'libiconv/1.17#fa54397801cd96911a8294bc5fc76335:41ad450120fdab2266b1185a967d298f7ae52595#cf7c954738a4a81fd68bf7671465b350'
Uploading package 'libiconv/1.17#fa54397801cd96911a8294bc5fc76335:76864d438e6a53828b8769476a7b57a241d91b69#75ffc5d59aea5a9fc7b41e07d4265f37'
Uploading package 'libiconv/1.17#fa54397801cd96911a8294bc5fc76335:a3c9d80d887539fac38b81ff8cd4585fe42027e0#23ff9eb9a19f9ec623af4c81fb1b717a'
Uploading package 'libiconv/1.17#fa54397801cd96911a8294bc5fc76335:abe5e2b04ea92ce2ee91bc9834317dbe66628206#3cbb797095f66828f6f09d715f77cb71'
Uploading package 'libiconv/1.17#fa54397801cd96911a8294bc5fc76335:ae9eaf478e918e6470fe64a4d8d4d9552b0b3606#669ec67f5e2341df39e0389e12421e77'
Uploading package 'libiconv/1.17#fa54397801cd96911a8294bc5fc76335:b647c43bfefae3f830561ca202b6cfd935b56205#fb0673713e76a055437cd2d225556268'
Uploading package 'libiconv/1.17#fa54397801cd96911a8294bc5fc76335:d62dff20d86436b9c58ddc0162499d197be9de1e#c230e582baef26b39e7451d02b5a5f7a'
Uploading package 'libiconv/1.17#fa54397801cd96911a8294bc5fc76335:dbb40f41e6e9a5c4a9a1fd8d9e6ccf6d92676c92#ba60c975bbf6ff7c6b93551e264c8927'
Uploading recipe 'meson/1.0.0#15586c0ac6f682805875ef903dbe7ee2'
Uploading package 'meson/1.0.0#15586c0ac6f682805875ef903dbe7ee2:da39a3ee5e6b4b0d3255bfef95601890afd80709#5c8fd51fc33f12e26519674d99afd0e5'
Uploading recipe 'ninja/1.11.1#a2f0b832705907016f336839f96963f8'
Uploading package 'ninja/1.11.1#a2f0b832705907016f336839f96963f8:3593751651824fb813502c69c971267624ced41a#a53f170b60a46aef75ead8658bdeae05'
Uploading package 'ninja/1.11.1#a2f0b832705907016f336839f96963f8:617cae191537b47386c088e07b1822d8606b7e67#c91372a33f74405b60f9f71b2163a290'
Uploading package 'ninja/1.11.1#a2f0b832705907016f336839f96963f8:723257509aee8a72faf021920c2874abc738e029#2af209f6b38a9f7b2c777c6bff456ffb'
Uploading package 'ninja/1.11.1#a2f0b832705907016f336839f96963f8:9ac8640923e5284645f8852ef8ba335654f4020e#0943503a21a3beb1238c0805dacc4d28'
Uploading recipe 'pkgconf/1.9.3#a920b5c7f8d04f22b9fe03db91a864dd'
Uploading package 'pkgconf/1.9.3#a920b5c7f8d04f22b9fe03db91a864dd:43771b8671ac44479c188dd72670e2eb2d7918a6#ce4d1d61f0b05d4229631aa740250685'
Uploading package 'pkgconf/1.9.3#a920b5c7f8d04f22b9fe03db91a864dd:8b5cf1367c351fd3c60ef4e28c1a50612761b13e#4ee5b12713113deadea85ed447d0e655'
Uploading package 'pkgconf/1.9.3#a920b5c7f8d04f22b9fe03db91a864dd:c0b621fd4b3199fe05075171573398833dba85f4#a231c33e360d8be4e90467b36b88f027'
Uploading package 'pkgconf/1.9.3#a920b5c7f8d04f22b9fe03db91a864dd:df7e47c8f0b96c79c977dd45ec51a050d8380273#ffb7995c86a762b52da14de294154467'
Uploading recipe 'bison/3.8.2#a8e86b304f8085ddbb22395c99a9a0a8'
Uploading package 'bison/3.8.2#a8e86b304f8085ddbb22395c99a9a0a8:500c2a3f502e0ca7d4a4c65cb2a4a0b0a24994f5#6e426a4fff8e364779169ab986a1daa3'
Uploading package 'bison/3.8.2#a8e86b304f8085ddbb22395c99a9a0a8:812844a246c05915dcfd8c471dbf04d2834dc0f9#b4ebb174a7c42d14419c51aa2be4480b'
Uploading package 'bison/3.8.2#a8e86b304f8085ddbb22395c99a9a0a8:9a523dd17a4da54882f7a1e363b21c4a141d314f#bf48544cf6e5037d1ed00c25a480c575'
Uploading recipe 'flex/2.6.4#e35bc44b3fcbcd661e0af0dc5b5b1ad4'
Uploading package 'flex/2.6.4#e35bc44b3fcbcd661e0af0dc5b5b1ad4:24612164eb0760405fcd237df0102e554ed1cb2f#324afa01f05f7e37fdbdc931357db407'
Uploading package 'flex/2.6.4#e35bc44b3fcbcd661e0af0dc5b5b1ad4:a3c9d80d887539fac38b81ff8cd4585fe42027e0#2ea834019a3a03dbaac1be5023e55ce6'
Uploading package 'flex/2.6.4#e35bc44b3fcbcd661e0af0dc5b5b1ad4:abe5e2b04ea92ce2ee91bc9834317dbe66628206#7602a676ca6bca378805ca1847eb617c'
Uploading package 'flex/2.6.4#e35bc44b3fcbcd661e0af0dc5b5b1ad4:b647c43bfefae3f830561ca202b6cfd935b56205#d18545ed84d684e0090595f1eb0d23c5'
Uploading package 'flex/2.6.4#e35bc44b3fcbcd661e0af0dc5b5b1ad4:d62dff20d86436b9c58ddc0162499d197be9de1e#f9fa036bc05554a2c016d6f42a27dc7b'
Uploading package 'flex/2.6.4#e35bc44b3fcbcd661e0af0dc5b5b1ad4:dbb40f41e6e9a5c4a9a1fd8d9e6ccf6d92676c92#8acda13cf8bf1f468de27db65531fedf'
Uploading recipe 'm4/1.4.19#c1c4b1ee919e34630bb9b50046253d3c'
Uploading package 'm4/1.4.19#c1c4b1ee919e34630bb9b50046253d3c:3593751651824fb813502c69c971267624ced41a#c69dc2230d016a77b5514d9916b14714'
Uploading package 'm4/1.4.19#c1c4b1ee919e34630bb9b50046253d3c:617cae191537b47386c088e07b1822d8606b7e67#af3bb664b82c4f616d3146625c5b4bd5'
Uploading package 'm4/1.4.19#c1c4b1ee919e34630bb9b50046253d3c:723257509aee8a72faf021920c2874abc738e029#0b5e50355c3e4e4e9e3434f96167ed09'
Uploading package 'm4/1.4.19#c1c4b1ee919e34630bb9b50046253d3c:9ac8640923e5284645f8852ef8ba335654f4020e#0b930e2019f5dfbf0c5e4ed8b8be9bf1'
</details>

Note that only the dependencies necessary for the current configuration will be computed and promoted.
It's possible that you might need to run this command several times with different profiles to gather all your wanted dependencies.