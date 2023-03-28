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
    run(f'conan remote add extensions-prod {os.getenv("ART_URL")}/api/conan/extensions-prod')
    run(f'conan remote add extensions-stg {os.getenv("ART_URL")}/api/conan/extensions-stg')

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

    build_name = "mybuildinfo"
    build_number = "1"

    run(f"conan config install {repo}")
    run("conan new cmake_lib -d name=mypkg -d version=1.0 --force")
    run("conan create . --format json > create.json")

    try:
        run("conan remove mypkg -c -r extensions-stg")
    except:
        pass

    run("conan upload mypkg/1.0 -c -r extensions-stg")
    run(f'conan art:property set {os.getenv("ART_URL")} extensions-stg mypkg/1.0 --property="build.name={build_name}" --property="build.number={build_number}" --user="{os.getenv("CONAN_LOGIN_USERNAME_EXTENSIONS_STG")}" --password="{os.getenv("CONAN_PASSWORD_EXTENSIONS_STG")}"')
    run(f'conan art:build-info create create.json {build_name} {build_number} > {build_name}.json')
    run(f'conan art:build-info upload {build_name}.json {os.getenv("ART_URL")} --user="{os.getenv("CONAN_LOGIN_USERNAME_EXTENSIONS_STG")}" --password="{os.getenv("CONAN_PASSWORD_EXTENSIONS_STG")}"')
