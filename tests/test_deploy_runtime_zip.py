import shutil
import tempfile
import os

import pytest

from tools import run


@pytest.fixture(autouse=True)
def conan_test():
    old_env = dict(os.environ)
    env_vars = {"CONAN_HOME": tempfile.mkdtemp(suffix="conans")}
    os.environ.update(env_vars)
    current = tempfile.mkdtemp(suffix="conans")
    cwd = os.getcwd()
    os.chdir(current)
    try:
        yield
    finally:
        os.chdir(cwd)
        os.environ.clear()
        os.environ.update(old_env)


def test_deploy_runtime_zip():
    repo = os.path.join(os.path.dirname(__file__), "..")
    run(f"conan config install {repo}")
    run("conan --help")

    # Let's build a application to bundle
    run("conan new cmake_exe --define name=hello --define version=0.1")
    run("conan profile detect")
    run("conan create .")

    run("conan install --requires hello/0.1 --deployer=runtime_zip_deploy")
    shutil.unpack_archive("runtime.zip", "zip_contents")
    dir_list = os.listdir("zip_contents")
    assert len(dir_list) == 1
    assert isinstance(dir_list[0], str) and dir_list[0].startswith("hello")


def test_deploy_runtime_zip_with_folder():
    repo = os.path.join(os.path.dirname(__file__), "..")
    run(f"conan config install {repo}")
    run("conan --help")

    # Let's build a application to bundle
    run("conan new cmake_exe --define name=hello --define version=0.1")
    # add additional folder for test case
    with open("CMakeLists.txt", "a") as f:
        f.write("""\n\nadd_executable(hello2 src/hello.cpp src/main.cpp)
install(TARGETS hello2 DESTINATION "."
        RUNTIME DESTINATION bin/folder
        ARCHIVE DESTINATION lib
        LIBRARY DESTINATION lib
        )""")
    run("conan profile detect")
    run("conan create .")

    run("conan install --requires hello/0.1 --deployer=runtime_zip_deploy")
    shutil.unpack_archive("runtime.zip", "zip_contents")
    dir_list = os.listdir("zip_contents")
    assert len(dir_list) == 2
    assert all(isinstance(dir_list_elem, str) and dir_list_elem.startswith("hello") for dir_list_elem in dir_list)
