## Recipe commands
These are commands that target recipes


#### [Bump dependencies](cmd_bump_deps.py)

For the recipe passed as parameter, it searches for new version of each requirement/build requirement/tool requirement, and updates the version of the dependency in the recipe.

> **Note:** The recipe does not have to be exported in cache.
> The recipe is not exported to local cache, and it is not built.

**Parameters**
- **path** _Optional_: Path to the recipe file (by default: current working directory)
- **remote** _Optional_: Remote repository to check for new versions of dependencies(by default: None).
- **cache** _Optional_: Search in the local cache(by default: True if no remote is passed).

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

#### [Create SBOM](cmd_create_sbom.py)

Creates an SBOM in CycloneDX 1.4 JSON format.
**This command is in an experimental stage, feedback is welcome.**

**Parameters**
* **format** _Required_: `cyclonedx_1.4_json`
* supports all other arguments used by `conan graph`, see `conan recipe:create-sbom --help`

**Dependencies**
The command requires the package `cyclonedx-python-lib`.
You can install it via
<!-- keep in sync with the error message that asks for requirements/dependencies in `cmd_create_sbom.py` -->
```shellSession
$ pip install 'cyclonedx-python-lib>=4.0.1,<5.0.0'
```

Usage:

```shellSession
$ cd conan-center-index/recipes/gmp/all
$ conan recipe:create-sbom -f cyclonedx_1.4_json .
{"components": [{"bom-ref": "pkg:conan/m4@1.4.19?rref=c1c4b1ee919e34630bb9b50046253d3c", "description": "GNU M4 is an implementation of the traditional Unix macro processor", "externalReferences": [{"type": "website", "url": "https://www.gnu.org/software/m4/"}], "licenses": [{"license": {"id": "GPL-3.0-only"}}], "name": "m4", "purl": "pkg:conan/m4@1.4.19?rref=c1c4b1ee919e34630bb9b50046253d3c", "type": "library", "version": "1.4.19"}], "dependencies": [{"dependsOn": ["pkg:conan/m4@1.4.19?rref=c1c4b1ee919e34630bb9b50046253d3c"], "ref": "pkg:conan/gmp"}, {"ref": "pkg:conan/m4@1.4.19?rref=c1c4b1ee919e34630bb9b50046253d3c"}], "metadata": {"component": {"bom-ref": "pkg:conan/gmp", "description": "GMP is a free library for arbitrary precision arithmetic, operating on signed integers, rational numbers, and floating-point numbers.", "externalReferences": [{"type": "website", "url": "https://gmplib.org"}], "licenses": [{"license": {"id": "GPL-2.0"}}, {"license": {"id": "LGPL-3.0"}}], "name": "gmp", "purl": "pkg:conan/gmp", "type": "library"}, "timestamp": "2023-08-08T12:55:48.275439+00:00", "tools": [{"externalReferences": [{"type": "build-system", "url": "https://github.com/CycloneDX/cyclonedx-python-lib/actions"}, {"type": "distribution", "url": "https://pypi.org/project/cyclonedx-python-lib/"}, {"type": "documentation", "url": "https://cyclonedx.github.io/cyclonedx-python-lib/"}, {"type": "issue-tracker", "url": "https://github.com/CycloneDX/cyclonedx-python-lib/issues"}, {"type": "license", "url": "https://github.com/CycloneDX/cyclonedx-python-lib/blob/main/LICENSE"}, {"type": "release-notes", "url": "https://github.com/CycloneDX/cyclonedx-python-lib/blob/main/CHANGELOG.md"}, {"type": "vcs", "url": "https://github.com/CycloneDX/cyclonedx-python-lib"}, {"type": "website", "url": "https://cyclonedx.org"}], "name": "cyclonedx-python-lib", "vendor": "CycloneDX", "version": "4.0.1"}]}, "serialNumber": "urn:uuid:b5b7a98b-e06a-4627-a520-2db2a4427daa", "version": 1, "$schema": "http://cyclonedx.org/schema/bom-1.4.schema.json", "bomFormat": "CycloneDX", "specVersion": "1.4"}
```

```shellSession
$ conan recipe:create-sbom -f cyclonedx_1.4_json --requires gmp/6.2.1
{"components": [{"bom-ref": "pkg:conan/gmp@6.2.1?rref=c0aec48648a7dff99f293870b95cad36", "description": "GMP is a free library for arbitrary precision arithmetic, operating on signed integers, rational numbers, and floating-point numbers.", "externalReferences": [{"type": "website", "url": "https://gmplib.org"}], "licenses": [{"license": {"id": "GPL-2.0"}}, {"license": {"id": "LGPL-3.0"}}], "name": "gmp", "purl": "pkg:conan/gmp@6.2.1?rref=c0aec48648a7dff99f293870b95cad36", "type": "library", "version": "6.2.1"}, {"bom-ref": "pkg:conan/m4@1.4.19?rref=c1c4b1ee919e34630bb9b50046253d3c", "description": "GNU M4 is an implementation of the traditional Unix macro processor", "externalReferences": [{"type": "website", "url": "https://www.gnu.org/software/m4/"}], "licenses": [{"license": {"id": "GPL-3.0-only"}}], "name": "m4", "purl": "pkg:conan/m4@1.4.19?rref=c1c4b1ee919e34630bb9b50046253d3c", "type": "library", "version": "1.4.19"}], "dependencies": [{"dependsOn": ["pkg:conan/gmp@6.2.1?rref=c0aec48648a7dff99f293870b95cad36"], "ref": "pkg:conan/UNKNOWN"}, {"dependsOn": ["pkg:conan/m4@1.4.19?rref=c1c4b1ee919e34630bb9b50046253d3c"], "ref": "pkg:conan/gmp@6.2.1?rref=c0aec48648a7dff99f293870b95cad36"}, {"ref": "pkg:conan/m4@1.4.19?rref=c1c4b1ee919e34630bb9b50046253d3c"}], "metadata": {"component": {"bom-ref": "pkg:conan/UNKNOWN", "name": "UNKNOWN", "purl": "pkg:conan/UNKNOWN", "type": "library"}, "timestamp": "2023-08-09T08:49:53.324361+00:00", "tools": [{"externalReferences": [{"type": "build-system", "url": "https://github.com/CycloneDX/cyclonedx-python-lib/actions"}, {"type": "distribution", "url": "https://pypi.org/project/cyclonedx-python-lib/"}, {"type": "documentation", "url": "https://cyclonedx.github.io/cyclonedx-python-lib/"}, {"type": "issue-tracker", "url": "https://github.com/CycloneDX/cyclonedx-python-lib/issues"}, {"type": "license", "url": "https://github.com/CycloneDX/cyclonedx-python-lib/blob/main/LICENSE"}, {"type": "release-notes", "url": "https://github.com/CycloneDX/cyclonedx-python-lib/blob/main/CHANGELOG.md"}, {"type": "vcs", "url": "https://github.com/CycloneDX/cyclonedx-python-lib"}, {"type": "website", "url": "https://cyclonedx.org"}], "name": "cyclonedx-python-lib", "vendor": "CycloneDX", "version": "4.0.1"}]}, "serialNumber": "urn:uuid:b1189a91-e92c-43ee-8ed5-a51e48d5aab9", "version": 1, "$schema": "http://cyclonedx.org/schema/bom-1.4.schema.json", "bomFormat": "CycloneDX", "specVersion": "1.4"}
```
