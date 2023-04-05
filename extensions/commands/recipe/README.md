## Recipe commands
These are commands that target recipes


#### [Bump dependencies](cmd_bump_deps.py)

For the recipe passed as parameter, it searches for new version of each requirement/build requirement/tool requirement, and updates the version of the dependency in the recipe.

> **Note:** The recipe does not have to be exported in cache.
> The recipe is not exported to local cache, and it is not built.

**Parameters**
- **path** _Optional_: Path to the recipe file (by default: current working directory)
- **remote** _Optional_: Remote repository to check for new versions of dependencies(by default: default conan remote).

```
$ conan recipe:bump-deps conan-center-index/recipes/qt/6.x.x/
updating cmake/3.25.2 to cmake/3.25.3 in conan-center-index/recipes/qt/6.x.x/conanfile.py:436
updating openssl/1.1.1s to openssl/3.1.0 in conan-center-index/recipes/qt/6.x.x/conanfile.py:365
updating pcre2/10.40 to pcre2/10.42 in conan-center-index/recipes/qt/6.x.x/conanfile.py:367
updating vulkan-loader/1.3.231.0 to vulkan-loader/1.3.239.0 in conan-center-index/recipes/qt/6.x.x/conanfile.py:369
updating glib/2.75.1 to glib/2.76.1 in conan-center-index/recipes/qt/6.x.x/conanfile.py:373
updating freetype/2.12.1 to freetype/2.13.0 in conan-center-index/recipes/qt/6.x.x/conanfile.py:377
updating harfbuzz/5.3.1 to harfbuzz/6.0.0 in conan-center-index/recipes/qt/6.x.x/conanfile.py:383
updating sqlite3/3.40.0 to sqlite3/3.41.1 in conan-center-index/recipes/qt/6.x.x/conanfile.py:392
updating libmysqlclient/8.0.30 to libmysqlclient/8.0.31 in conan-center-index/recipes/qt/6.x.x/conanfile.py:395
updating libpq/14.5 to libpq/14.7 in conan-center-index/recipes/qt/6.x.x/conanfile.py:397
updating xkbcommon/1.4.1 to xkbcommon/1.5.0 in conan-center-index/recipes/qt/6.x.x/conanfile.py:406
updating zstd/1.5.2 to zstd/1.5.5 in conan-center-index/recipes/qt/6.x.x/conanfile.py:411
updating xkbcommon/1.4.1 to xkbcommon/1.5.0 in conan-center-index/recipes/qt/6.x.x/conanfile.py:413
updating nss/3.85 to nss/3.89 in conan-center-index/recipes/qt/6.x.x/conanfile.py:422
WARN: Error bumping krb5/1.18.3 in conan-center-index/recipes/qt/6.x.x/conanfile.py:431
WARN: Unable to bump non constant dependency in conan-center-index/recipes/qt/6.x.x/conanfile.py:456
updating moltenvk/1.2.0 to moltenvk/1.2.2 in conan-center-index/recipes/qt/6.x.x/conanfile.py:371
updating libjpeg-turbo/2.1.4 to libjpeg-turbo/2.1.5 in conan-center-index/recipes/qt/6.x.x/conanfile.py:386
Successfully bumped the dependencies of recipe conan-center-index/recipes/qt/6.x.x/conanfile.py
```
