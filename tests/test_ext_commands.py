import os
import textwrap

import pytest
from conan.test.utils.tools import TestClient


@pytest.fixture(scope="package")
def client():
    tc = TestClient(light=True,
                    default_server_user=True,
                    custom_commands_folder=os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                                        os.path.pardir, "extensions", "commands"))
    conanfile = textwrap.dedent("""
        import os
        import time
        from conan import ConanFile
        from conan.tools.files import save

        class Pkg(ConanFile):
            version = "1.0"
            def package(self):
                save(self, os.path.join(self.package_folder, "file.txt"), str(time.time()))
        """)
    tc.save({"conanfile.py": conanfile})

    tc.run("create --name=hello")
    tc.run("create --name=hello")
    tc.run("create --name=greetings")
    tc.run("create --name=greetings")

    tc.run("create --name=bye")
    tc.run("upload '*:*#*' -c -r default")
    return tc


@pytest.mark.parametrize("remote", [True, False])
@pytest.mark.parametrize("pattern", ["*:*", "*:*#*"])
def test_check_prev_patterns_find(client, pattern, remote):
    remote = "-r default" if remote else ""
    client.run(f"ext:check-prevs {pattern} {remote}", assert_error=True)
    assert "ERROR: Multiple package revisions found" in client.out
    assert "bye/1.0" not in client.out
    assert "hello/1.0" in client.out
    assert "greetings/1.0" in client.out


@pytest.mark.parametrize("pattern", ["bye/1.0:*", "bye/1.0:*#*"])
def test_check_prev_patterns_no_find(client, pattern):
    client.run(f"ext:check-prevs {pattern} -r default")
    assert "ERROR: Multiple package revisions found" not in client.out
    assert "bye/1.0" not in client.out
    assert "hello/1.0" not in client.out
    assert "greetings/1.0" not in client.out


@pytest.mark.parametrize("pattern", ["*:*", "*:*#*"])
def test_check_prev_pkglist_find(client, pattern):
    client.run(f"list {pattern} -r default -f=json", redirect_stdout="list.json")
    client.run(f"ext:check-prevs -l list.json", assert_error=True)
    assert "ERROR: Multiple package revisions found" in client.out
    assert "bye/1.0" not in client.out
    assert "hello/1.0" in client.out
    assert "greetings/1.0" in client.out


@pytest.mark.parametrize("pattern", ["bye/1.0:*", "bye/1.0:*#*"])
def test_check_prev_pkglist_no_find(client, pattern):
    client.run(f"list {pattern} -r default -f=json", redirect_stdout="list.json")
    client.run(f"ext:check-prevs -l list.json")
    assert "ERROR: Multiple package revisions found" not in client.out
    assert "bye/1.0" not in client.out
    assert "hello/1.0" not in client.out
    assert "greetings/1.0" not in client.out


def test_check_prev_errors(client):
    client.run("ext:check-prevs * -l list.json", assert_error=True)
    assert 'ERROR: Cannot define both the pattern and the package list file' in client.out

    client.run(f"ext:check-prevs hello/1.0 -r default", assert_error=True)
    assert "ERROR: Multiple package revisions found" not in client.out
    assert "ERROR: The pattern must include a package_id" in client.out
