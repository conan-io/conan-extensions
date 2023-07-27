# Deployers

- Runtime Zipper

```sh
$ conan install --requires=fmt/10.0.0 -o="fmt/*:shared=True" --deployer=runtime_zip_deploy
# ...
======== Computing necessary packages ========
Requirements
    fmt/10.0.0#dd5e3eb81b512a1bb34a5aab88a07e82:a54b21e862b2638e704927807d06df018d4514c5#df013771a6193a12440274931cd966e8 - Cache

======== Installing packages ========
fmt/10.0.0: Already installed! (1 of 1)

======== Finalizing install (deploy, generators) ========
Install finished successfully
$ unzip runtime.zip 
Archive:  runtime.zip
  inflating: libfmt.dylib            
  inflating: libfmt.10.0.0.dylib     
  inflating: libfmt.10.dylib
```

- Licenses Zipper

```sh
$ conan install --requires=restinio/0.6.15 --deployer=licenses
# ...
======== Installing packages ========
asio/1.22.1: Already installed! (1 of 8)
expected-lite/0.6.3: Already installed! (2 of 8)
fmt/8.1.1: Already installed! (3 of 8)
http_parser/2.9.4: Already installed! (4 of 8)
optional-lite/3.5.0: Already installed! (5 of 8)
string-view-lite/1.6.0: Already installed! (6 of 8)
variant-lite/2.0.0: Already installed! (7 of 8)
restinio/0.6.15: Already installed! (8 of 8)

======== Finalizing install (deploy, generators) ========
cli: Generating aggregated env files
cli: Generated aggregated env files: ['conanbuild.sh', 'conanrun.sh']
Install finished successfully
$ unzip -l licenses.zip
Archive:  licenses.zip
  Length      Date    Time    Name
---------  ---------- -----   ----
     1575  05-25-2022 23:38   restinio/0.6.15/LICENSE
     1077  03-24-2020 03:54   http_parser/2.9.4/LICENSE-MIT
     1408  07-17-2023 11:26   fmt/8.1.1/LICENSE.rst
     1338  03-21-2023 06:40   expected-lite/0.6.3/LICENSE.txt
     1338  09-19-2021 01:17   optional-lite/3.5.0/LICENSE.txt
     1338  10-09-2020 07:01   string-view-lite/1.6.0/LICENSE.txt
     1338  11-08-2020 13:51   variant-lite/2.0.0/LICENSE.txt
     1338  03-15-2022 16:16   asio/1.22.1/LICENSE_1_0.txt
```
