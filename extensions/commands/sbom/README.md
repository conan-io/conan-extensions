## [Create SBOM](cmd_create_sbom.py)

Creates an SBOM in CycloneDX format.
**This command is in an experimental stage, feedback is welcome.**

**Parameters**
* `sbom_format` _Required_:  `1.4_json`, `1.3_json`, `1.2_json`, `1.4_xml`, `1.3_xml`, `1.2_xml`, `1.1_xml`, or `1.0_xml`
* supports all other arguments used by `conan graph`, see `conan recipe:create-sbom --help`

**Dependencies**
The command requires the package `cyclonedx-python-lib`.
You can install it via
<!-- keep in sync with the error message that asks for requirements/dependencies in `cmd_cyclonedx.py` -->
```shellSession
$ pip install 'cyclonedx-python-lib>=3.1.5,<5.0.0'
```

Usage:

```shellSession
$ cd conan-center-index/recipes/gmp/all
$ conan sbom:cyclonedx --sbom_format 1.4_json .
{"components": [{"bom-ref": "pkg:conan/m4@1.4.19?rref=c1c4b1ee919e34630bb9b50046253d3c", "description": "GNU M4 is an implementation of the traditional Unix macro processor", "externalReferences": [{"type": "website", "url": "https://www.gnu.org/software/m4/"}], "licenses": [{"license": {"id": "GPL-3.0-only"}}], "name": "m4", "purl": "pkg:conan/m4@1.4.19?rref=c1c4b1ee919e34630bb9b50046253d3c", "type": "library", "version": "1.4.19"}], "dependencies": [{"dependsOn": ["pkg:conan/m4@1.4.19?rref=c1c4b1ee919e34630bb9b50046253d3c"], "ref": "pkg:conan/gmp"}, {"ref": "pkg:conan/m4@1.4.19?rref=c1c4b1ee919e34630bb9b50046253d3c"}], "metadata": {"component": {"bom-ref": "pkg:conan/gmp", "description": "GMP is a free library for arbitrary precision arithmetic, operating on signed integers, rational numbers, and floating-point numbers.", "externalReferences": [{"type": "website", "url": "https://gmplib.org"}], "licenses": [{"license": {"id": "GPL-2.0"}}, {"license": {"id": "LGPL-3.0"}}], "name": "gmp", "purl": "pkg:conan/gmp", "type": "library"}, "timestamp": "2023-08-08T12:55:48.275439+00:00", "tools": [{"externalReferences": [{"type": "build-system", "url": "https://github.com/CycloneDX/cyclonedx-python-lib/actions"}, {"type": "distribution", "url": "https://pypi.org/project/cyclonedx-python-lib/"}, {"type": "documentation", "url": "https://cyclonedx.github.io/cyclonedx-python-lib/"}, {"type": "issue-tracker", "url": "https://github.com/CycloneDX/cyclonedx-python-lib/issues"}, {"type": "license", "url": "https://github.com/CycloneDX/cyclonedx-python-lib/blob/main/LICENSE"}, {"type": "release-notes", "url": "https://github.com/CycloneDX/cyclonedx-python-lib/blob/main/CHANGELOG.md"}, {"type": "vcs", "url": "https://github.com/CycloneDX/cyclonedx-python-lib"}, {"type": "website", "url": "https://cyclonedx.org"}], "name": "cyclonedx-python-lib", "vendor": "CycloneDX", "version": "4.0.1"}]}, "serialNumber": "urn:uuid:b5b7a98b-e06a-4627-a520-2db2a4427daa", "version": 1, "$schema": "http://cyclonedx.org/schema/bom-1.4.schema.json", "bomFormat": "CycloneDX", "specVersion": "1.4"}
```

```shellSession
$ conan sbom:cyclonedx --sbom_format 1.4_json --requires gmp/6.2.1
{"components": [{"bom-ref": "pkg:conan/gmp@6.2.1?rref=c0aec48648a7dff99f293870b95cad36", "description": "GMP is a free library for arbitrary precision arithmetic, operating on signed integers, rational numbers, and floating-point numbers.", "externalReferences": [{"type": "website", "url": "https://gmplib.org"}], "licenses": [{"license": {"id": "GPL-2.0"}}, {"license": {"id": "LGPL-3.0"}}], "name": "gmp", "purl": "pkg:conan/gmp@6.2.1?rref=c0aec48648a7dff99f293870b95cad36", "type": "library", "version": "6.2.1"}, {"bom-ref": "pkg:conan/m4@1.4.19?rref=c1c4b1ee919e34630bb9b50046253d3c", "description": "GNU M4 is an implementation of the traditional Unix macro processor", "externalReferences": [{"type": "website", "url": "https://www.gnu.org/software/m4/"}], "licenses": [{"license": {"id": "GPL-3.0-only"}}], "name": "m4", "purl": "pkg:conan/m4@1.4.19?rref=c1c4b1ee919e34630bb9b50046253d3c", "type": "library", "version": "1.4.19"}], "dependencies": [{"dependsOn": ["pkg:conan/gmp@6.2.1?rref=c0aec48648a7dff99f293870b95cad36"], "ref": "pkg:conan/UNKNOWN"}, {"dependsOn": ["pkg:conan/m4@1.4.19?rref=c1c4b1ee919e34630bb9b50046253d3c"], "ref": "pkg:conan/gmp@6.2.1?rref=c0aec48648a7dff99f293870b95cad36"}, {"ref": "pkg:conan/m4@1.4.19?rref=c1c4b1ee919e34630bb9b50046253d3c"}], "metadata": {"component": {"bom-ref": "pkg:conan/UNKNOWN", "name": "UNKNOWN", "purl": "pkg:conan/UNKNOWN", "type": "library"}, "timestamp": "2023-08-09T08:49:53.324361+00:00", "tools": [{"externalReferences": [{"type": "build-system", "url": "https://github.com/CycloneDX/cyclonedx-python-lib/actions"}, {"type": "distribution", "url": "https://pypi.org/project/cyclonedx-python-lib/"}, {"type": "documentation", "url": "https://cyclonedx.github.io/cyclonedx-python-lib/"}, {"type": "issue-tracker", "url": "https://github.com/CycloneDX/cyclonedx-python-lib/issues"}, {"type": "license", "url": "https://github.com/CycloneDX/cyclonedx-python-lib/blob/main/LICENSE"}, {"type": "release-notes", "url": "https://github.com/CycloneDX/cyclonedx-python-lib/blob/main/CHANGELOG.md"}, {"type": "vcs", "url": "https://github.com/CycloneDX/cyclonedx-python-lib"}, {"type": "website", "url": "https://cyclonedx.org"}], "name": "cyclonedx-python-lib", "vendor": "CycloneDX", "version": "4.0.1"}]}, "serialNumber": "urn:uuid:b1189a91-e92c-43ee-8ed5-a51e48d5aab9", "version": 1, "$schema": "http://cyclonedx.org/schema/bom-1.4.schema.json", "bomFormat": "CycloneDX", "specVersion": "1.4"}
```
