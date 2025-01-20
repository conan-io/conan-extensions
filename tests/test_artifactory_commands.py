import os
import json
import tempfile
import textwrap

from tools import run, save
from conan.tools.scm import Version
from conan import conan_version

import pytest

# to test locally with an Artifactory instance that already has
# extensions-stg and extensions-prod repos, define these environment variables

#     "CONAN_LOGIN_USERNAME_EXTENSIONS_PROD": "......",
#     "CONAN_PASSWORD_EXTENSIONS_PROD": "......",
#     "CONAN_LOGIN_USERNAME_EXTENSIONS_STG": "......",
#     "CONAN_PASSWORD_EXTENSIONS_STG": "......",
#     "ART_URL": "https://url/artifactory",


@pytest.fixture(autouse=True)
def conan_test():
    old_env = dict(os.environ)
    env_vars = {"CONAN_HOME": tempfile.mkdtemp(suffix='conans')}
    os.environ.update(env_vars)
    current = tempfile.mkdtemp(suffix="conans")
    cwd = os.getcwd()
    os.chdir(current)
    run("conan profile detect")
    run("conan remove '*' -c")

    out = run("conan remote list")

    if "extensions-stg" not in out:
        run(f'conan remote add extensions-stg {os.getenv("ART_URL")}/api/conan/extensions-stg')

    if "extensions-prod" not in out:
        run(f'conan remote add extensions-prod {os.getenv("ART_URL")}/api/conan/extensions-prod')

    run(f'conan remote login extensions-stg "{os.getenv("CONAN_LOGIN_USERNAME_EXTENSIONS_STG")}" -p "{os.getenv("CONAN_PASSWORD_EXTENSIONS_STG")}"')
    run(f'conan remote login extensions-prod "{os.getenv("CONAN_LOGIN_USERNAME_EXTENSIONS_PROD")}" -p "{os.getenv("CONAN_PASSWORD_EXTENSIONS_PROD")}"')
    # Install extension commands (this repo)
    repo = os.path.join(os.path.dirname(__file__), "..")
    run(f"conan config install {repo}")

    run("conan remove '*' -c -r extensions-stg")
    run("conan remove '*' -c -r extensions-prod")

    try:
        yield
    finally:
        run("conan remove '*' -c -r extensions-stg")
        run("conan remove '*' -c -r extensions-prod")
        os.chdir(cwd)
        os.environ.clear()
        os.environ.update(old_env)


@pytest.mark.requires_credentials
def test_build_info_create_no_deps():

    build_name = "mybuildinfo"
    build_number = "1"

    # Configure Artifactory server and credentials
    run(f'conan art:server add artifactory {os.getenv("ART_URL")} --user="{os.getenv("CONAN_LOGIN_USERNAME_EXTENSIONS_STG")}" --password="{os.getenv("CONAN_PASSWORD_EXTENSIONS_STG")}"')
    
    # Generate recipe to work with
    run("conan new cmake_lib -d name=mypkg -d version=1.0 --force")

    # Create release packages & build info and upload them
    run("conan create . --format json -tf='' -s build_type=Release > create_release.json")
    run("conan upload mypkg/1.0 -c -r extensions-stg")
    run(f'conan art:build-info create create_release.json {build_name}_release {build_number} extensions-stg > {build_name}_release.json')
    run(f'conan art:build-info upload {build_name}_release.json --server artifactory')

    # Create debug packages & build info and upload them
    run("conan create . --format json -tf='' -s build_type=Debug > create_debug.json")
    run("conan upload mypkg/1.0 -c -r extensions-stg")
    run(f'conan art:build-info create create_debug.json {build_name}_debug {build_number} extensions-stg > {build_name}_debug.json')
    run(f'conan art:build-info upload {build_name}_debug.json --url="{os.getenv("ART_URL")}" --user="{os.getenv("CONAN_LOGIN_USERNAME_EXTENSIONS_STG")}" --password="{os.getenv("CONAN_PASSWORD_EXTENSIONS_STG")}"')

    # Aggregate the release and debug build infos into a new one to later do the promotion
    run(f'conan art:build-info append {build_name}_aggregated {build_number} --server artifactory --build-info={build_name}_release,{build_number} --build-info={build_name}_debug,{build_number} > {build_name}_aggregated.json')
    run(f'conan art:build-info upload {build_name}_aggregated.json --url="{os.getenv("ART_URL")}" --user="{os.getenv("CONAN_LOGIN_USERNAME_EXTENSIONS_STG")}" --password="{os.getenv("CONAN_PASSWORD_EXTENSIONS_STG")}"')


    # Check the build infos are uploaded
    out = run(f'conan art:build-info get {build_name}_release {build_number} --server artifactory')
    assert '"name" : "mybuildinfo_release"' in out
    out = run(f'conan art:build-info get {build_name}_debug {build_number} --url="{os.getenv("ART_URL")}" --user="{os.getenv("CONAN_LOGIN_USERNAME_EXTENSIONS_STG")}" --password="{os.getenv("CONAN_PASSWORD_EXTENSIONS_STG")}"')
    assert '"name" : "mybuildinfo_debug"' in out
    out = run(f'conan art:build-info get {build_name}_aggregated {build_number} --server artifactory')
    assert '"name" : "mybuildinfo_aggregated"' in out

    run(f'conan art:build-info promote {build_name}_aggregated {build_number} extensions-stg extensions-prod --url="{os.getenv("ART_URL")}" --user="{os.getenv("CONAN_LOGIN_USERNAME_EXTENSIONS_STG")}" --password="{os.getenv("CONAN_PASSWORD_EXTENSIONS_STG")}"')

    # Clean cache to make sure package comes from artifactory later
    run('conan remove mypkg* -c')

    # we have to remove the package from the source repo because in the Conan promotion we copy
    # Conan promotions must always be copy, and the clean must be handled manually
    # otherwise you can end up deleting recipe artifacts that other packages use
    run('conan remove mypkg* -c -r extensions-stg')

    run('conan list "*#*:*#*" -r extensions-prod')

    run('conan list "*#*:*#*" -r extensions-stg')

    # Check that we can install from the prod repo after the promotion
    run('conan install --requires=mypkg/1.0 -r extensions-prod -s build_type=Release')
    run('conan install --requires=mypkg/1.0 -r extensions-prod -s build_type=Debug')

    # Check that build-infos can be removed from arifactory
    run(f'conan art:build-info delete {build_name}_release --server artifactory --build-number={build_number} --delete-all --delete-artifacts')
    run(f'conan art:build-info delete {build_name}_debug --server artifactory --build-number={build_number} --delete-all --delete-artifacts')
    run(f'conan art:build-info delete {build_name}_aggregated --url="{os.getenv("ART_URL")}" --build-number={build_number} --user="{os.getenv("CONAN_LOGIN_USERNAME_EXTENSIONS_STG")}" --password="{os.getenv("CONAN_PASSWORD_EXTENSIONS_STG")}" --delete-all --delete-artifacts')

    # Finally clean the artifactory repo (Deleting the build infos does not remove pacakges from repos)
    run('conan remove mypkg* -c -r extensions-prod')


@pytest.mark.requires_credentials
def test_build_info_create_with_build_url():

    build_name = "mybuildinfo"
    build_number = "1"
    build_url = "https://foo.org"

    # Configure Artifactory server and credentials
    run(f'conan art:server add artifactory {os.getenv("ART_URL")} --user="{os.getenv("CONAN_LOGIN_USERNAME_EXTENSIONS_STG")}" --password="{os.getenv("CONAN_PASSWORD_EXTENSIONS_STG")}"')
    
    # Generate recipe to work with
    run("conan new cmake_lib -d name=mypkg -d version=1.0 --force")

    # Create release packages & build info and upload them
    run("conan create . --format json -tf='' -s build_type=Release > create_release.json")
    run("conan upload mypkg/1.0 -c -r extensions-stg")
    out = run(f'conan art:build-info create create_release.json {build_name}_release {build_number} --build-url={build_url} extensions-stg')
    assert build_url in out


@pytest.mark.requires_credentials
def test_build_info_create_deps():
    #         +-------+
    #         | libc  |
    #         +-------+
    #             |
    #      +------+------+ 
    #      |             |
    #  +---+---+     +---+---+
    #  | liba  |     | libb  |
    #  +---+---+     +---+---+
    #      |             |
    #      +-------+-----+
    #              |
    #           +--+--+
    #           |mypkg|
    #           +-----+

    # Make sure artifactory repos are empty before starting the test
    run("conan remove mypkg* -c -r extensions-stg")
    run("conan remove mypkg* -c -r extensions-prod")

    build_name = "mybuildinfo"
    build_number = "1"

    run(f'conan art:server add artifactory {os.getenv("ART_URL")} --user="{os.getenv("CONAN_LOGIN_USERNAME_EXTENSIONS_STG")}" --password="{os.getenv("CONAN_PASSWORD_EXTENSIONS_STG")}"')

    # Create dependency packages and upload them
    run("conan new cmake_lib -d name=libc -d version=1.0 --force")
    run("conan create . -tf='' -s build_type=Release")
    run("conan create . -tf='' -s build_type=Debug")
    run("conan new cmake_lib -d name=liba -d version=1.0 -d requires=libc/1.0 --force")
    run("conan create . -tf='' -s build_type=Release")
    run("conan create . -tf='' -s build_type=Debug")
    run("conan new cmake_lib -d name=libb -d version=1.0 -d requires=libc/1.0 --force")
    run("conan create . -tf='' -s build_type=Release")
    run("conan create . -tf='' -s build_type=Debug")

    run("conan upload '*' -c -r extensions-stg")
    # we want to make sure that metadata from liba, libb and libc comes from Artifactory
    run("conan remove '*' -c")

    # Create the consumer pacakges with their build info and upload them to Artifactory
    run("conan new cmake_lib -d name=mypkg -d version=1.0 -d requires=liba/1.0 -d requires=libb/1.0 --force")

    run("conan create . --format json -tf='' -s build_type=Release --build=missing > create_release.json")
    run("conan upload 'mypkg/1.0' -c -r extensions-stg")
    run(f'conan art:build-info create create_release.json {build_name}_release {build_number} extensions-stg --server artifactory --with-dependencies > {build_name}_release.json')
    out = run(f'conan art:build-info upload {build_name}_release.json --server artifactory')
    assert "Build info uploaded successfully." in out

    run("conan create . --format json -tf='' -s build_type=Debug --build=missing > create_debug.json")
    run("conan upload 'mypkg/1.0' -c -r extensions-stg")
    run(f'conan art:build-info create create_debug.json {build_name}_debug {build_number} extensions-stg --url={os.getenv("ART_URL")} --user="{os.getenv("CONAN_LOGIN_USERNAME_EXTENSIONS_STG")}" --password="{os.getenv("CONAN_PASSWORD_EXTENSIONS_STG")}" --with-dependencies > {build_name}_debug.json')
    run(f'conan art:build-info upload {build_name}_debug.json --url="{os.getenv("ART_URL")}" --user="{os.getenv("CONAN_LOGIN_USERNAME_EXTENSIONS_STG")}" --password="{os.getenv("CONAN_PASSWORD_EXTENSIONS_STG")}"')

    # Aggregate build infos and upload the new one
    run(f'conan art:build-info append {build_name}_aggregated {build_number} --server artifactory --build-info={build_name}_release,{build_number} --build-info={build_name}_debug,{build_number} > {build_name}_aggregated.json')
    run(f'conan art:build-info upload {build_name}_aggregated.json --url="{os.getenv("ART_URL")}" --user="{os.getenv("CONAN_LOGIN_USERNAME_EXTENSIONS_STG")}" --password="{os.getenv("CONAN_PASSWORD_EXTENSIONS_STG")}"')

    # Check all build infos exist
    out = run(f'conan art:build-info get {build_name}_release {build_number} --server artifactory')
    assert '"name" : "mybuildinfo_release"' in out
    out = run(f'conan art:build-info get {build_name}_debug {build_number} --server artifactory')
    assert '"name" : "mybuildinfo_debug"' in out
    out = run(f'conan art:build-info get {build_name}_aggregated {build_number} --url="{os.getenv("ART_URL")}" --user="{os.getenv("CONAN_LOGIN_USERNAME_EXTENSIONS_STG")}" --password="{os.getenv("CONAN_PASSWORD_EXTENSIONS_STG")}"')
    assert '"name" : "mybuildinfo_aggregated"' in out

    # FIXME: commenting this part, promote with --dependencies does not work
    # wait until it's fixed or the new BuildInfo promotion is released

    #run(f'conan art:build-info promote {build_name}_aggregated {build_number} {os.getenv("ART_URL")} extensions-stg extensions-prod --user="{os.getenv("CONAN_LOGIN_USERNAME_EXTENSIONS_STG")}" --password="{os.getenv("CONAN_PASSWORD_EXTENSIONS_STG")}" --dependencies')

    # Try to install the package and pick the dependencies from prod, it should work
    # but apparently some conaninfos are not promoted and fails
    # it could be because those are files that have the same hash 

    # run(f'conan remove liba/1.0 -r=extensions-stg')
    # run(f'conan remove libc/1.0 -r=extensions-stg')
    # run(f'conan remove mypkg/1.0 -r=extensions-stg')
    # run(f'conan remove "*" -c')

    # run(f'conan install --requires=mypkg/1.0')

    # Promotions using Release Bundles do work with depdendencies, but they are not implemented in the testing Artifactory
    # conan art:build-info create-bundle ${build_name}_aggregated.json develop full_bundle 1.0 ${ART_URL} test_key_pair --user=${CONAN_LOGIN_USERNAME_DEVELOP} --password="${CONAN_PASSWORD_DEVELOP}"

    # Remove build-infos to clean artifactory
    run(f'conan art:build-info delete {build_name}_release --build-number={build_number} --server="artifactory" --delete-all --delete-artifacts')
    run(f'conan art:build-info delete {build_name}_debug --build-number={build_number} --url="{os.getenv("ART_URL")}" --user="{os.getenv("CONAN_LOGIN_USERNAME_EXTENSIONS_STG")}" --password="{os.getenv("CONAN_PASSWORD_EXTENSIONS_STG")}" --delete-all --delete-artifacts')
    run(f'conan art:build-info delete {build_name}_aggregated --build-number={build_number} --url="{os.getenv("ART_URL")}" --user="{os.getenv("CONAN_LOGIN_USERNAME_EXTENSIONS_STG")}" --password="{os.getenv("CONAN_PASSWORD_EXTENSIONS_STG")}" --delete-all --delete-artifacts')


@pytest.mark.requires_credentials
def test_build_info_create_from_cached_deps():
    # Make sure artifactory repos are empty before starting the test
    run("conan remove mypkg* -c -r extensions-stg")
    run("conan remove mypkg* -c -r extensions-prod")

    run(f'conan art:server add artifactory {os.getenv("ART_URL")} --user="{os.getenv("CONAN_LOGIN_USERNAME_EXTENSIONS_STG")}" --password="{os.getenv("CONAN_PASSWORD_EXTENSIONS_STG")}"')

    # Create dependency packages and upload them
    run("conan new cmake_lib -d name=libc -d version=1.0 --force")
    run("conan create . -tf=''")
    run("conan new cmake_lib -d name=liba -d version=1.0 -d requires=libc/1.0 --force")
    run("conan create . -tf=''")

    run("conan upload '*' --dry-run -c -r extensions-stg")

    # libc node in graph is cached
    run("conan install . --format json > install_release.json")

    run(f'conan art:build-info create install_release.json bi_release 1 extensions-stg --server artifactory --with-dependencies > bi_release.json')

    with open("bi_release.json", "r") as file:
        build_info = json.load(file)

    assert len(build_info.get("modules")) == 0

    run(f'conan art:build-info create install_release.json bi_release 1 extensions-stg --server artifactory --with-dependencies --add-cached-deps > bi_release.json')

    with open("bi_release.json", "r") as file:
        build_info = json.load(file)

    assert len(build_info.get("modules")) == 2


@pytest.mark.requires_credentials
def test_fail_if_not_uploaded():
    """
    In order to create the Build Info we need the hashes of the artifacts that are uploaded
    to Artifactory, but those artifacts: conan_source.tgz, conan_package.tgz, etc.
    are only created on the upload process, that's why we need an upload previous to 
    creating the Build Infos. If those artifacts are not in the cache, we raise.
    """

    # Make sure artifactory repos are empty before starting the test
    run("conan remove mypkg* -c -r extensions-stg")
    run("conan remove mypkg* -c -r extensions-prod")

    build_name = "mybuildinfo"
    build_number = "1"

    run("conan new cmake_lib -d name=mypkg -d version=1.0 --force")
    run("conan create . -tf='' -s build_type=Release")


@pytest.mark.requires_credentials
def test_build_info_project():
    """
    Test that build info is correctly manages using a project in Artifactory
    """
    # Make sure artifactory repos are empty before starting the test
    run("conan remove mypkg* -c -r extensions-stg")
    run("conan remove mypkg* -c -r extensions-prod")

    # Configure Artifactory server and credentials
    run(f'conan art:server add artifactory {os.getenv("ART_URL")} --user="{os.getenv("CONAN_LOGIN_USERNAME_EXTENSIONS_STG")}" --password="{os.getenv("CONAN_PASSWORD_EXTENSIONS_STG")}"')

    build_name = "mybuildinfoproject"
    build_number = "1"
    project = "extensions-testing"

    run("conan new cmake_lib -d name=mypkg -d version=1.0 --force")

    run("conan create . --format json -tf='' > create.json")

    run(f'conan art:build-info create create.json {build_name} {build_number} extensions-stg', error=True)
    run("conan upload 'mypkg/1.0' -c -r extensions-stg")
    run(f'conan art:build-info create create.json {build_name} {build_number} extensions-stg --server artifactory --with-dependencies > {build_name}.json')
    run(f'conan art:build-info upload {build_name}.json --server artifactory --project {project}')

    out = run(f'conan art:build-info get {build_name} {build_number} --project {project} --server artifactory')
    assert '"name" : "mybuildinfoproject"' in out
    run(f'conan art:build-info get {build_name} {build_number} --server artifactory', error=True)

    run(f'conan art:build-info append {build_name}_aggregated {build_number} --server artifactory --build-info={build_name},{build_number} --project {project} > {build_name}_aggregated.json')
    run(f'conan art:build-info upload {build_name}_aggregated.json --server artifactory --project {project}')

    run(f'conan art:build-info promote {build_name}_aggregated {build_number} extensions-stg extensions-prod --server artifactory --project {project} --comment "Promoting using build-info in project"')

    run('conan remove mypkg* -c')
    run('conan remove mypkg* -c -r extensions-stg')
    run('conan install --requires=mypkg/1.0 -r extensions-prod')

    run(f'conan art:build-info delete {build_name} --build-number={build_number} --server artifactory --project {project}')
    run(f'conan art:build-info delete {build_name}_aggregated --delete-all --delete-artifacts --server artifactory --project {project}')


@pytest.mark.requires_credentials
def test_build_info_dependency_different_repo():
    """
    Test that build info is correctly generated for a package with dependencies in a different repo in Artifactory
    """
    #         +-------+
    #         | liba  |
    #         +-------+
    #             |
    #          +--+--+
    #          |mypkg|
    #          +-----+

    # Make sure artifactory repos are empty before starting the test
    run("conan remove mypkg* -c -r extensions-stg")
    run("conan remove mypkg* -c -r extensions-prod")

    # Configure Artifactory server and credentials
    run(f'conan art:server add artifactory {os.getenv("ART_URL")} --user="{os.getenv("CONAN_LOGIN_USERNAME_EXTENSIONS_STG")}" --password="{os.getenv("CONAN_PASSWORD_EXTENSIONS_STG")}"')

    build_name = "buildinfoprojectwithdependencyuploadedtoadifferentrepo"
    build_number = "1"
    project = "extensions-testing"

    # Create dependency packages and upload them
    run("conan new cmake_lib -d name=liba -d version=1.0 --force")
    run("conan create . -tf=''")

    # Upload dependency to separated repo and remove from local cache
    run("conan upload liba/1.0 -r extensions-prod")
    run('conan remove liba* -c')

    # Create consumer
    run("conan new cmake_lib -d name=mypkg -d version=1.0 -d requires=liba/1.0 --force")
    run("conan create . --format json -tf='' > create.json")

    # Upload consumer to another repo
    run("conan upload mypkg/1.0 -r extensions-stg")

    # Create build info
    run(f'conan art:build-info create create.json {build_name} {build_number} extensions-stg --server artifactory --with-dependencies > {build_name}.json')
    run(f'conan art:build-info upload {build_name}.json --server artifactory')

    out = run(f'conan art:build-info get {build_name} {build_number} --server artifactory')
    assert '"name" : "buildinfoprojectwithdependencyuploadedtoadifferentrepo"' in out

    run('conan remove mypkg* -c')
    run('conan remove mypkg* -c -r extensions-stg')
    run('conan remove liba* -c -r extensions-prod')

    run(f'conan art:build-info delete {build_name} --build-number={build_number} --server artifactory')


@pytest.mark.requires_credentials
def test_server_complete():
    """
    Test server add, list, remove commands
    """

    # Make sure artifactory repos are empty before starting the test
    run("conan remove mypkg* -c -r extensions-stg")
    run("conan remove mypkg* -c -r extensions-prod")

    server_url = os.getenv("ART_URL")
    server_user = os.getenv("CONAN_LOGIN_USERNAME_EXTENSIONS_STG")

    out_add = run(f'conan art:server add server1 {server_url} --user="{server_user}" --password="{os.getenv("CONAN_PASSWORD_EXTENSIONS_STG")}"')

    assert f"Server 'server1' ({server_url}) added successfully" in out_add

    out_list = run('conan art:server list')

    assert "server1:" in out_list
    assert f"url: {server_url}" in out_list
    assert f"user: {server_user}" in out_list
    assert "password: ***" in out_list

    out_remove = run('conan art:server remove server1')

    assert f"Server 'server1' ({server_url}) removed successfully" in out_remove


@pytest.mark.requires_credentials
def test_server_add_error():
    """
    Test server add error when adding a server with same name
    """

    # Make sure artifactory repos are empty before starting the test
    run("conan remove mypkg* -c -r extensions-stg")
    run("conan remove mypkg* -c -r extensions-prod")

    try:
        run("conan art:server remove server1")  # Make sure the server is not configured
    except:
        pass
    server_url = os.getenv("ART_URL")
    server_user = os.getenv("CONAN_LOGIN_USERNAME_EXTENSIONS_STG")

    run(f'conan art:server add server1 {server_url} --user="{server_user}" --password="{os.getenv("CONAN_PASSWORD_EXTENSIONS_STG")}"')
    out_add = run(f'conan art:server add server1 other_url --user="other_user" --password="other_pass"', error=True)

    assert f"Server 'server1' ({server_url}) already exist." in out_add


@pytest.mark.requires_credentials
def test_server_remove_error():
    """
    Test server remove errors when there is no server with the provided name
    """
    out = run("conan art:server remove server1", error=True)

    assert "Server 'server1' does not exist." in out


@pytest.mark.requires_credentials
def test_server_list_empty():
    """
    Test server list output when no servers are configured
    """
    out = run("conan art:server list")

    assert "No servers configured. Use `conan art:server add` command to add one." in out


@pytest.mark.requires_credentials
def test_add_server_token():
    """
    Test server add with token
    """

    # Make sure artifactory repos are empty before starting the test
    run("conan remove mypkg* -c -r extensions-stg")
    run("conan remove mypkg* -c -r extensions-prod")

    server_url = os.getenv("ART_URL")
    server_user = os.getenv("CONAN_LOGIN_USERNAME_EXTENSIONS_STG")
    token = os.getenv("ARTIFACTORY_TOKEN")

    out_add = run(f'conan art:server add server1 {server_url} --user="{server_user}" --token="{token}"')

    assert f"Server 'server1' ({server_url}) added successfully" in out_add


@pytest.mark.requires_credentials
def test_art_promote_timestamps():
    conanfile = textwrap.dedent("""
    from conan import ConanFile

    class Pkg(ConanFile):
        name = "mypkg"
        version = "1.0"
    """)
    save("./conanfile.py", conanfile)

    run("conan create .")
    out = run("conan list mypkg/1.0:*#* -f=json")
    local_list_json_out = json.loads(out)
    local_recipe_timestamp = local_list_json_out["Local Cache"]["mypkg/1.0"]["revisions"]["9d6b6bdeb9bb50a31acc8f970f562b3c"]["timestamp"]
    local_package_timestamp = local_list_json_out["Local Cache"]["mypkg/1.0"]["revisions"]["9d6b6bdeb9bb50a31acc8f970f562b3c"]["packages"]["da39a3ee5e6b4b0d3255bfef95601890afd80709"]["revisions"]["0ba8627bd47edc3a501e8f0eb9a79e5e"]["timestamp"]
    run("conan upload mypkg/1.0 -c -r extensions-stg")

    out = run("conan list mypkg/1.0:*#* -r=extensions-stg -f=json", stderr=None)
    remote_stg_list_json_out = json.loads(out)
    remote_stg_recipe_timestamp = remote_stg_list_json_out["extensions-stg"]["mypkg/1.0"]["revisions"]["9d6b6bdeb9bb50a31acc8f970f562b3c"]["timestamp"]
    remote_stg_package_timestamp = remote_stg_list_json_out["extensions-stg"]["mypkg/1.0"]["revisions"]["9d6b6bdeb9bb50a31acc8f970f562b3c"]["packages"]["da39a3ee5e6b4b0d3255bfef95601890afd80709"]["revisions"]["0ba8627bd47edc3a501e8f0eb9a79e5e"]["timestamp"]

    assert local_recipe_timestamp != remote_stg_recipe_timestamp
    assert local_package_timestamp != remote_stg_package_timestamp

    save("pkglist.json", out)

    art_url = os.getenv("ART_URL")
    art_user = os.getenv("CONAN_LOGIN_USERNAME_EXTENSIONS_PROD")
    art_password = os.getenv("CONAN_PASSWORD_EXTENSIONS_PROD")
    run(f"conan art:promote pkglist.json --from=extensions-stg --to=extensions-prod --url={art_url} --user={art_user} --password={art_password}")

    out = run("conan list mypkg/1.0:*#* -r=extensions-prod -f=json", stderr=None)
    remote_prod_list_json_out = json.loads(out)
    remote_prod_recipe_timestamp = remote_prod_list_json_out["extensions-prod"]["mypkg/1.0"]["revisions"]["9d6b6bdeb9bb50a31acc8f970f562b3c"]["timestamp"]
    remote_prod_package_timestamp = remote_prod_list_json_out["extensions-prod"]["mypkg/1.0"]["revisions"]["9d6b6bdeb9bb50a31acc8f970f562b3c"]["packages"]["da39a3ee5e6b4b0d3255bfef95601890afd80709"]["revisions"]["0ba8627bd47edc3a501e8f0eb9a79e5e"]["timestamp"]

    assert remote_stg_recipe_timestamp == remote_prod_recipe_timestamp
    assert remote_stg_package_timestamp == remote_prod_package_timestamp
