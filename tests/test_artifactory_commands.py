import tempfile
import os


from tools import run


import pytest


@pytest.fixture(autouse=True)
def conan_test():
    old_env = dict(os.environ)
    env_vars = {"CONAN_HOME": tempfile.mkdtemp(suffix='conans')}
    os.environ.update(env_vars)
    current = tempfile.mkdtemp(suffix="conans")
    cwd = os.getcwd()
    os.chdir(current)

    run("conan profile detect")
    run("conan remote add extensions-prod https://conanv2beta.jfrog.io/artifactory/api/conan/extensions-prod")
    run("conan remote add extensions-stg https://conanv2beta.jfrog.io/artifactory/api/conan/extensions-stg")

    try:
        yield
    finally:
        os.chdir(cwd)
        os.environ.clear()
        os.environ.update(old_env)


def run(cmd):
    ret = os.system(cmd)
    if ret != 0:
        raise Exception(f"Failed CMD: {cmd}")


def test_build_info_create():
    repo = os.path.join(os.path.dirname(__file__), "..")

    run(f"conan config install {repo}")
    run("conan new cmake_lib -d name=mypkg -d version=1.0 --force")
    run("conan create . --format json > create.json")
    run("conan remove mypkg -c -r extensions-stg")
    run("conan upload mypkg/1.0 -c -r extensions-stg")
    run("conan art:build-info create create.json test_bi_create 1 > buildinfo.json")
    run(f'conan art:property set https://conanv2beta.jfrog.io/artifactory extensions-stg mypkg/1.0 --property="build.name=test_bi_create" --property="build.number=1" --user={os.getenv("CONAN_LOGIN_USERNAME_EXTENSIONS_STG")} --password={os.getenv("CONAN_PASSWORD_EXTENSIONS_STG")}')
    run(f'conan art:build-info upload buildinfo.json https://conanv2beta.jfrog.io/artifactory --user={os.getenv("CONAN_LOGIN_USERNAME_EXTENSIONS_STG")} --password={os.getenv("CONAN_PASSWORD_EXTENSIONS_STG")}')
