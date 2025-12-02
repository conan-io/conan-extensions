## Binary manipulation commands

### Creating universal binaries

```bash
conan install --requires=mylibrary/1.0 --deployer=full_deploy -s arch=armv8
conan install --requires=mylibrary/1.0 --deployer=full_deploy -s arch=x86_64
conan bin:lipo create full_deploy/host --output-folder=universal
```
