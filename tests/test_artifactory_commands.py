import os
import json
import sys
import tempfile
import textwrap

from tools import load, run, save
from conan.tools.scm import Version
from conan import conan_version

import pytest
import requests

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

    if "third-party" not in out:
        run(f'conan remote add third-party {os.getenv("ART_URL")}/api/conan/third-party')

    run(f'conan remote login extensions-stg "{os.getenv("CONAN_LOGIN_USERNAME_EXTENSIONS_STG")}" -p "{os.getenv("CONAN_PASSWORD_EXTENSIONS_STG")}"')
    run(f'conan remote login extensions-prod "{os.getenv("CONAN_LOGIN_USERNAME_EXTENSIONS_PROD")}" -p "{os.getenv("CONAN_PASSWORD_EXTENSIONS_PROD")}"')
    run(f'conan remote login third-party "{os.getenv("CONAN_LOGIN_USERNAME_EXTENSIONS_PROD")}" -p "{os.getenv("CONAN_PASSWORD_EXTENSIONS_PROD")}"')
    # Install extension commands (this repo)
    repo = os.path.join(os.path.dirname(__file__), "..")
    run(f"conan config install {repo}")

    run("conan remove '*' -c -r extensions-stg")
    run("conan remove '*' -c -r extensions-prod")
    run("conan remove '*' -c -r third-party")

    try:
        yield
    finally:
        run("conan remove '*' -c -r extensions-stg")
        run("conan remove '*' -c -r extensions-prod")
        run("conan remove '*' -c -r third-party")
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
def test_build_info_export_pkg():

    # Configure Artifactory server and credentials
    run(f'conan art:server add artifactory {os.getenv("ART_URL")} --user="{os.getenv("CONAN_LOGIN_USERNAME_EXTENSIONS_STG")}" --password="{os.getenv("CONAN_PASSWORD_EXTENSIONS_STG")}"')
    
    # Generate recipe to work with
    run("conan new cmake_lib -d name=mypkg -d version=1.0 --force")

    run("conan build .")

    # Create release packages & build info and upload them
    run("conan export-pkg . --format json -tf='' > export.json")
    run("conan upload mypkg/1.0 -c -r extensions-stg")
    run(f'conan art:build-info create export.json mybuildinfo 1 extensions-stg --server=artifactory --out-file=mybuildinfo.json')

    build_info = json.loads(load("mybuildinfo.json"))

    mypkg_modules = [m for m in build_info["modules"] if "mypkg/1.0#294e801a0e1da10084441487e95b80e8" in m.get("id")]
    assert len(mypkg_modules) == 2  # Assert both recipe and package modules exist
    mypkg_recipe_module = next(m for m in mypkg_modules if m.get("id") == "mypkg/1.0#294e801a0e1da10084441487e95b80e8")
    assert len(mypkg_recipe_module["artifacts"]) == 3  # Assert the 3 artifacts exist
    mypkg_conanmanifest_data = next(
        artifact for artifact in mypkg_recipe_module["artifacts"]
        if artifact.get("name") == "conanmanifest.txt"
    )  # Assert conanmanifest.txt path
    assert mypkg_conanmanifest_data[
               "path"] == "extensions-stg/_/mypkg/1.0/_/294e801a0e1da10084441487e95b80e8/export/conanmanifest.txt"
    mypkg_sources_data = next(
        artifact for artifact in mypkg_recipe_module["artifacts"]
        if artifact.get("name") == "conan_sources.tgz"
    )  # Assert conan_sources.tgz path
    assert mypkg_sources_data[
               "path"] == "extensions-stg/_/mypkg/1.0/_/294e801a0e1da10084441487e95b80e8/export/conan_sources.tgz"
    mypkg_conanfile_data = next(
        artifact for artifact in mypkg_recipe_module["artifacts"]
        if artifact.get("name") == "conanfile.py"
    )  # Assert conanfile.py path
    assert mypkg_conanfile_data[
               "path"] == "extensions-stg/_/mypkg/1.0/_/294e801a0e1da10084441487e95b80e8/export/conanfile.py"


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
    out = run(f'conan art:build-info upload {build_name}_debug.json --server artifactory')
    assert "Build info uploaded successfully." in out

    # Aggregate build infos (one from remote, one from local file) and upload the new one
    run(f'conan art:build-info append {build_name}_aggregated {build_number} --server artifactory --build-info={build_name}_release,{build_number} --build-info-file={build_name}_debug.json > {build_name}_aggregated.json')
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

    run(f'conan art:build-info bundle-create full_bundle 1.0 --server="artifactory" test_key_pair --build-info={build_name}_release,{build_number} --build-info={build_name}_debug,{build_number}')
    run(f'conan art:build-info bundle-delete full_bundle 1.0 --server="artifactory"')

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


#@pytest.mark.requires_credentials
@pytest.mark.xfail(reason="Token not configured in CI yet")
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
def test_build_info_promote_continue_on_error():
    # Make sure artifactory repos are empty before starting the test
    run("conan remove mypkg* -c -r extensions-stg")
    run("conan remove mypkg* -c -r extensions-prod")

    # Configure Artifactory server and credentials
    run(f'conan art:server add artifactory {os.getenv("ART_URL")} --user="{os.getenv("CONAN_LOGIN_USERNAME_EXTENSIONS_STG")}" --password="{os.getenv("CONAN_PASSWORD_EXTENSIONS_STG")}"')

    build_name = "otherbuildinfopromote"
    build_number = "1"
    project = "extensions-testing"

    run("conan new cmake_lib -d name=mypkg -d version=1.0 --force")
    run("conan create . --format json -tf='' > create.json")
    run("conan upload 'mypkg/1.0' -c -r extensions-stg")

    run(f'conan art:build-info create create.json {build_name} {build_number} extensions-stg --server artifactory > {build_name}.json')
    run(f'conan art:build-info upload {build_name}.json --server artifactory')
    # Remove package (not recipe) to force promotion fail
    run("conan remove 'mypkg/1.0:*' -c -r extensions-stg")
    out = run(f'conan art:build-info promote {build_name} {build_number} extensions-stg extensions-prod --server artifactory', error=True)
    assert "ERROR: 400: Unable to find artifacts of build 'otherbuildinfopromote' #1 from artifactory-build-info repo: aborting promotion." in out
    out = run(f'conan art:build-info promote {build_name} {build_number} extensions-stg extensions-prod --server artifactory --continue-on-error')
    assert "Handling copy/move of file: extensions-prod/_/mypkg/1.0/_/294e801a0e1da10084441487e95b80e8/export/conanfile.py" in out

    run('conan remove mypkg* -c')
    run('conan remove mypkg* -c -r extensions-stg')
    run('conan remove mypkg* -c -r extensions-prod')

    run(f'conan art:build-info delete {build_name} --delete-all --delete-artifacts --server artifactory')


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
def test_build_info_dependency_from_extra_repo():
    """
    Tests that the build-info correctly attributes a dependency's path
    to the repository it was found in.
    """
    #         +-------+
    #         | dep   | (from third-party repo)
    #         +-------+
    #             |
    #          +--+--+
    #          | pkg | (from extensions-stg repo)
    #          +-----+


    # Make sure artifactory repos are empty before starting the test
    run("conan remove mypkg* -c -r extensions-stg")
    run("conan remove mypkg* -c -r third-party")

    # Configure Artifactory server and credentials
    run(f'conan art:server add artifactory {os.getenv("ART_URL")} --user="{os.getenv("CONAN_LOGIN_USERNAME_EXTENSIONS_STG")}" --password="{os.getenv("CONAN_PASSWORD_EXTENSIONS_STG")}"')

    # Create dependency and upload it to the 'third-party' repo
    run("conan new cmake_lib -d name=dep -d version=1.0 --force")
    run("conan create .")
    run("conan upload dep/1.0 -c -r third-party")
    run("conan remove dep/1.0 -c")  # Ensure it's not in the local cache

    # Create consumer package that requires the dependency
    run("conan new cmake_lib -d name=pkg -d version=1.0 -d requires=dep/1.0 --force")
    # Create the package, it will download 'dep' from 'third-party'
    run("conan create . --format=json > create.json")
    run("conan upload pkg/1.0 -c -r extensions-stg")

    # Create the build-info, specifying the extra repository
    build_name = "build_with_extra_repo"
    build_number = "1"
    run(f'conan art:build-info create create.json {build_name} {build_number} extensions-stg third-party '
        f'--with-dependencies --add-cached-deps '
        f'--server=artifactory > {build_name}.json')

    # Verify the generated build-info
    with open(f"{build_name}.json", "r") as f:
        build_info = json.load(f)

    modules = build_info.get("modules", [])
    
    # Find the module for the dependency 'dep/1.0'
    dep_module = None
    for module in modules:
        if module.get("id", "").startswith("dep/1.0"):
            dep_module = module
            break

    assert dep_module is not None, "Dependency 'dep/1.0' not found in build-info modules"

    # Check that the path of its artifacts points to the 'third-party' repo
    for artifact in dep_module.get("artifacts", []):
        path = artifact.get("path", "")
        assert path.startswith("third-party/"), \
            f"Artifact path '{path}' should start with 'third-party/'"

    # Clean up
    run(f"conan remove '*' -c -r third-party")
    run(f"conan remove '*' -c -r extensions-stg")


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


#@pytest.mark.requires_credentials
@pytest.mark.xfail(reason="Token not configured in CI yet")
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


class TestArtPromoteCommand:
    @staticmethod
    def _art_credentials():
        return (os.getenv("ART_URL"), os.getenv("CONAN_LOGIN_USERNAME_EXTENSIONS_PROD"),
                os.getenv("CONAN_PASSWORD_EXTENSIONS_PROD"))

    @pytest.fixture(params=[False, True], ids=["recipe-folder", "update-recipes"])
    def update_recipes(self, request):
        """ Runs the test promoting the recipes by copying their whole folder (the default),
        and file by file (--update-recipes) """
        return request.param

    def _promote(self, *args, update_recipes=False, **kwargs):
        """ Promotes pkglist.json from extensions-stg to extensions-prod, returns the output """
        art_url, art_user, art_password = self._art_credentials()
        if update_recipes:
            args += ("--update-recipes",)
        return run(f"conan art:promote pkglist.json --from=extensions-stg --to=extensions-prod "
                   f"--url={art_url} --user={art_user} --password={art_password} {' '.join(args)}", **kwargs)

    def _art_files(self, repository, folder):
        """ Files in the folder of the Artifactory repository (recursively), relative to the folder """
        art_url, art_user, art_password = self._art_credentials()
        response = requests.get(f"{art_url}/api/storage/{repository}/{folder}?list&deep=1",
                                auth=(art_user, art_password))
        response.raise_for_status()
        return {item["uri"] for item in response.json()["files"]}

    @staticmethod
    def _local_refs(name_version="mypkg/1.0"):
        """ Recipe and package references, with revisions, of the only package in the local cache """
        run(f'conan list "{name_version}:*#*" -f=json --out-file=local.json')
        revisions = json.loads(load("local.json"))["Local Cache"][name_version]["revisions"]
        rrev, recipe = next(iter(revisions.items()))
        package_id, package = next(iter(recipe["packages"].items()))
        prev = next(iter(package["revisions"]))
        return f"{name_version}#{rrev}", f"{name_version}#{rrev}:{package_id}#{prev}"

    @staticmethod
    def _recipe_folder(rref):
        name_version, rrev = rref.split("#")
        return f"_/{name_version}/_/{rrev}/export"

    @staticmethod
    def _package_folder(pref):
        rref, package = pref.split(":")
        package_id, prev = package.split("#")
        name_version, rrev = rref.split("#")
        return f"_/{name_version}/_/{rrev}/package/{package_id}/{prev}"

    @staticmethod
    def _save_metadata(ref, files):
        """ Creates metadata files (a dict of name: content) in the local cache for the recipe or package ref """
        folder = run(f"conan cache path {ref} --folder=metadata").rstrip()
        for name, content in files.items():
            save(os.path.join(folder, name), content)

    @staticmethod
    def _download_metadata(rref, pref):
        """ Downloads from extensions-prod to an empty cache, returns the recipe and package metadata folders """
        run('conan remove "*" -c')
        run('conan download "mypkg/1.0:*#*" -r=extensions-prod --metadata="*"')
        return (run(f"conan cache path {rref} --folder=metadata").rstrip(),
                run(f"conan cache path {pref} --folder=metadata").rstrip())

    @staticmethod
    def _assert_promoted(pattern="mypkg/1.0:*#*"):
        """ Checks that what is in pkglist.json (listed in extensions-stg with the pattern) is now
        in extensions-prod, with the same revisions and timestamps """
        run(f'conan list "{pattern}" -r=extensions-prod -f=json --out-file=promoted.json')
        promoted = json.loads(load("promoted.json"))["extensions-prod"]
        assert promoted == json.loads(load("pkglist.json"))["extensions-stg"]

    def _art_delete(self, repository, path):
        """ Deletes a file from the Artifactory repository """
        art_url, art_user, art_password = self._art_credentials()
        requests.delete(f"{art_url}/{repository}/{path}", auth=(art_user, art_password)).raise_for_status()

    def _create_and_upload(self):
        """ Creates mypkg/1.0, uploads it to extensions-stg and lists it there in pkglist.json.
        Returns its recipe and package references, with revisions """
        conanfile = textwrap.dedent("""
            from conan import ConanFile

            class Pkg(ConanFile):
                name = "mypkg"
                version = "1.0"
            """)
        save("./conanfile.py", conanfile)
        run("conan create .")
        rref, pref = self._local_refs()
        run("conan upload mypkg/1.0 -c -r extensions-stg")
        run('conan list "mypkg/1.0:*#*" -r=extensions-stg -f=json --out-file=pkglist.json')
        return rref, pref

    @pytest.mark.requires_credentials
    def test_art_promote_timestamps(self, update_recipes):
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

        self._promote(update_recipes=update_recipes)

        out = run("conan list mypkg/1.0:*#* -r=extensions-prod -f=json", stderr=None)
        remote_prod_list_json_out = json.loads(out)
        remote_prod_recipe_timestamp = remote_prod_list_json_out["extensions-prod"]["mypkg/1.0"]["revisions"]["9d6b6bdeb9bb50a31acc8f970f562b3c"]["timestamp"]
        remote_prod_package_timestamp = remote_prod_list_json_out["extensions-prod"]["mypkg/1.0"]["revisions"]["9d6b6bdeb9bb50a31acc8f970f562b3c"]["packages"]["da39a3ee5e6b4b0d3255bfef95601890afd80709"]["revisions"]["0ba8627bd47edc3a501e8f0eb9a79e5e"]["timestamp"]

        assert remote_stg_recipe_timestamp == remote_prod_recipe_timestamp
        assert remote_stg_package_timestamp == remote_prod_package_timestamp

    @pytest.mark.requires_credentials
    def test_art_promote_build_version(self, update_recipes):
        conanfile = textwrap.dedent("""
            from conan import ConanFile
    
            class Pkg(ConanFile):
                name = "mypkg"
                version = "1.0+build"
            """)
        save("./conanfile.py", conanfile)

        run("conan create .")
        run("conan upload mypkg/1.0+build --format json --out-file pkglist.json -c -r extensions-stg")

        # promote package extensions-stg => extensions-prod
        self._promote(update_recipes=update_recipes)

        # check that package is available in extensions-prod
        out = run("conan list mypkg/1.0+build:*#* -r=extensions-prod -f=json", stderr=None)
        remote_prod_list_json = json.loads(out)
        assert "extensions-prod" in remote_prod_list_json
        assert "mypkg/1.0+build" in remote_prod_list_json["extensions-prod"]

    @pytest.mark.requires_credentials
    def test_art_promote_python_requires(self, update_recipes):
        conanfile = textwrap.dedent("""
            from conan import ConanFile

            class Pkg(ConanFile):
                name = "mypkg"
                version = "1.0"
                package_type = "python-require"
            """)
        save("./conanfile.py", conanfile)

        run("conan create .")
        run("conan upload mypkg/1.0 -c -r extensions-stg")

        run("conan list mypkg/1.0:*#* -r=extensions-stg -f=json --out-file=pkglist.json")

        self._promote(update_recipes=update_recipes)
        self._assert_promoted()

    @pytest.mark.requires_credentials
    @pytest.mark.parametrize("compress", [None, "gz", "zst", "xz"])
    def test_art_promote_different_compressions(self, compress, update_recipes):
        if compress == "zst" and sys.version_info.minor < 14:
            pytest.skip("Skipping zst compression tests")

        conf = f"-cc core.upload:compression_format={compress}" if compress else ""
        conanfile = textwrap.dedent("""
                from conan import ConanFile

                class Pkg(ConanFile):
                    name = "mypkg"
                    version = "1.0"
                """)
        save("./conanfile.py", conanfile)

        run(f"conan create . {conf}")
        run(f"conan upload mypkg/1.0 -c -r extensions-stg {conf} -vvv")
        run(f'conan remove "*" -c {conf}')

        run(f"conan list mypkg/1.0:*#* -r=extensions-stg -f=json --out-file=pkglist.json {conf}")

        self._promote(update_recipes=update_recipes)

        out = run(f"conan list mypkg/1.0:*#* -r=extensions-prod -f=json {conf}", stderr=None)
        assert "da39a3ee5e6b4b0d3255bfef95601890afd80709" in out
        run(f"conan download mypkg/1.0:*#* -r=extensions-prod {conf} -vvv")

        # And lastly, just in case
        run(f"conan cache check-integrity mypkg/1.0:*#* {conf}")

    @pytest.mark.requires_credentials
    def test_art_promote_metadata(self, update_recipes):
        conanfile = textwrap.dedent("""
            from conan import ConanFile

            class Pkg(ConanFile):
                name = "mypkg"
                version = "1.0"
            """)
        save("./conanfile.py", conanfile)

        run("conan create .")
        rref, pref = self._local_refs()
        self._save_metadata(rref, {"base_recipe.txt": "recipe metadata"})
        self._save_metadata(pref, {"base_package.txt": "package metadata"})
        run("conan upload mypkg/1.0 -c -r extensions-stg")

        run('conan list "mypkg/1.0:*#*" -r=extensions-stg -f=json --out-file=pkglist.json')
        self._promote(update_recipes=update_recipes)

        out = run('conan list "mypkg/1.0:*#*" -r=extensions-prod -f=compact', stderr=None)
        assert pref.rsplit('#', 1)[0] in out

        recipe_metadata, package_metadata = self._download_metadata(rref, pref)
        assert load(os.path.join(recipe_metadata, "base_recipe.txt")) == "recipe metadata"
        assert load(os.path.join(package_metadata, "base_package.txt")) == "package metadata"

        # The metadata can change without a new revision, and new files can be added
        self._save_metadata(rref, {"base_recipe.txt": "recipe metadata overwritten",
                              "base_recipe_new.txt": "recipe metadata new"})
        self._save_metadata(pref, {"base_package.txt": "package metadata overwritten",
                              "base_package_new.txt": "package metadata new"})
        run('conan upload mypkg/1.0 -c -r extensions-stg --metadata="*"')

        # The new files are promoted, but the ones that already existed are not overwritten.
        # The recipe revision is already in the destination: its new files are only promoted
        # if the recipe files are promoted one by one, else it is skipped as a whole
        out = self._promote(update_recipes=update_recipes)
        assert "Destination already exists, skipping" in out
        recipe_metadata, package_metadata = self._download_metadata(rref, pref)
        assert load(os.path.join(package_metadata, "base_package_new.txt")) == "package metadata new"
        assert load(os.path.join(package_metadata, "base_package.txt")) == "package metadata"
        assert load(os.path.join(recipe_metadata, "base_recipe.txt")) == "recipe metadata"
        new_recipe_file = os.path.join(recipe_metadata, "base_recipe_new.txt")
        assert os.path.exists(new_recipe_file) == update_recipes
        if update_recipes:
            assert load(new_recipe_file) == "recipe metadata new"

        # Now force, and overwrite. The recipe is also only overwritten if its files are promoted one by one
        out = self._promote("--force", update_recipes=update_recipes)
        assert "Destination already exists, overwriting (--force)" in out
        recipe_metadata, package_metadata = self._download_metadata(rref, pref)
        assert load(os.path.join(package_metadata, "base_package_new.txt")) == "package metadata new"
        assert load(os.path.join(package_metadata, "base_package.txt")) == "package metadata overwritten"
        assert os.path.exists(os.path.join(recipe_metadata, "base_recipe_new.txt")) == update_recipes
        assert load(os.path.join(recipe_metadata, "base_recipe.txt")) == (
            "recipe metadata overwritten" if update_recipes else "recipe metadata")

    @pytest.mark.requires_credentials
    def test_art_promote_tarballs(self, update_recipes):
        conanfile = textwrap.dedent("""
            from conan import ConanFile
            from conan.tools.files import save
            import os

            class Pkg(ConanFile):
                name = "mypkg"
                version = "1.0"
                exports_sources = "CMakeLists.txt"
                def source(self):
                    self.output.info("Conandata version: {}".format(self.conan_data["version"]))
            """)
        save("./conanfile.py", conanfile)
        save("./conandata.yml", "version: 1\n")
        save("./CMakeLists.txt", "cmake_minimum_required(VERSION 3.15)")

        run("conan create .")
        run("conan upload mypkg/1.0 -c -r extensions-stg")
        run("conan remove '*' -c")

        run('conan list "mypkg/1.0:*#*" -r=extensions-stg -f=json --out-file=pkglist.json')
        self._promote(update_recipes=update_recipes)
        self._assert_promoted()

        out = run("conan install --requires=mypkg/1.0 -r=extensions-prod -b='&'")
        # Conandata is there
        assert "Conandata version: 1" in out

    @pytest.mark.requires_credentials
    @pytest.mark.parametrize("compress", [None, "gz", "xz", "zst"])
    def test_art_promote_complete_revision(self, compress, update_recipes):
        """ Every file of the recipe and package revisions is promoted, not just a known set of them:
        the tarballs with the exports and the sources, the binary and all the metadata, even if nested """
        if compress == "zst" and sys.version_info.minor < 14:
            pytest.skip("Skipping zst compression tests")

        conf = f"-cc core.upload:compression_format={compress}" if compress else ""
        extension = {None: "tgz", "gz": "tgz", "xz": "txz", "zst": "tzst"}[compress]
        conanfile = textwrap.dedent("""
            from conan import ConanFile

            class Pkg(ConanFile):
                name = "mypkg"
                version = "1.0"
                exports = "extra/*"
                exports_sources = "src/*"
            """)
        save("./conanfile.py", conanfile)
        save("./conandata.yml", "version: 1\n")
        save("./extra/helper.txt", "exported")
        save("./src/main.cpp", "int main() {}")

        run(f"conan create . {conf}")
        rref, pref = self._local_refs()
        for ref in (rref, pref):
            self._save_metadata(ref, {"base.txt": "metadata", "logs/build.log": "nested metadata"})
        run(f"conan upload mypkg/1.0 -c -r extensions-stg {conf}")
        run('conan list "mypkg/1.0:*#*" -r=extensions-stg -f=json --out-file=pkglist.json')

        # Make sure the origin does have all of these, or the comparisons below could not fail
        recipe_files = self._art_files("extensions-stg", self._recipe_folder(rref))
        assert {f"/conan_export.{extension}", f"/conan_sources.{extension}",
                "/metadata/base.txt", "/metadata/logs/build.log"} <= recipe_files
        package_files = self._art_files("extensions-stg", self._package_folder(pref))
        assert {f"/conan_package.{extension}", "/metadata/base.txt", "/metadata/logs/build.log"} <= package_files

        def assert_same_files_in_destination():
            for folder in (self._recipe_folder(rref), self._package_folder(pref)):
                assert self._art_files("extensions-prod", folder) == self._art_files("extensions-stg", folder)

        self._promote(update_recipes=update_recipes)
        assert_same_files_in_destination()
        # Nothing changes promoting it again, nor if it is forced
        self._promote(update_recipes=update_recipes)
        assert_same_files_in_destination()
        self._promote("--force", update_recipes=update_recipes)
        assert_same_files_in_destination()

        # And it is a valid package for the ones using it
        run('conan remove "*" -c')
        run("conan install --requires=mypkg/1.0 -r=extensions-prod")
        run('conan cache check-integrity "mypkg/1.0:*#*"')

        # A recipe revision in the destination that misses a file is only completed if the recipe files
        # are promoted one by one, else it is skipped as a whole
        missing = f"/conan_sources.{extension}"
        self._art_delete("extensions-prod", f"{self._recipe_folder(rref)}{missing}")
        self._promote(update_recipes=update_recipes)
        assert (missing in self._art_files("extensions-prod", self._recipe_folder(rref))) == update_recipes

    @pytest.mark.requires_credentials
    @pytest.mark.parametrize("kind", ["recipe", "package"])
    def test_art_promote_revision_not_found_in_origin(self, kind, update_recipes):
        rref, pref = self._create_and_upload()

        # Not in the origin anymore: only the packages, or the recipe with them
        run(f'conan remove "{rref}:*" -c -r=extensions-stg' if kind == "package"
            else f'conan remove "{rref}" -c -r=extensions-stg')

        out = self._promote(update_recipes=update_recipes, error=True)
        if kind == "package":
            assert f"Package {pref} not found in the 'extensions-stg' repository" in out
        elif update_recipes:
            assert f"Recipe {rref} not found in the 'extensions-stg' repository" in out
        else:
            # Copying the whole folder does not look for the recipe before, the copy is the one failing
            assert f"Failed to promote {self._recipe_folder(rref)}/" in out

    @pytest.mark.requires_credentials
    # Copying the whole folder of the recipe does not check that the recipe is complete
    @pytest.mark.parametrize("kind, update_recipes", [("recipe", True), ("package", False), ("package", True)],
                             ids=["recipe-update-recipes", "package-recipe-folder", "package-update-recipes"])
    def test_art_promote_incomplete_revision_in_origin(self, kind, update_recipes):
        rref, pref = self._create_and_upload()
        ref, folder, file = ((rref, self._recipe_folder(rref), "conanmanifest.txt") if kind == "recipe"
                             else (pref, self._package_folder(pref), "conaninfo.txt"))
        self._art_delete("extensions-stg", f"{folder}/{file}")

        out = self._promote(update_recipes=update_recipes, error=True)
        assert f"{kind.capitalize()} {ref} is missing {file} in the 'extensions-stg' repository" in out

    @pytest.mark.requires_credentials
    def test_art_promote_invalid_input(self):
        save("pkglist.json", "{}")

        out = run("conan art:promote pkglist.json --from=extensions-stg --to=extensions-prod", error=True)
        assert "Specify --server or --url" in out

        out = self._promote(error=True)
        assert "Can't promote empty package list pkglist.json" in out


@pytest.mark.requires_credentials
def test_property_value_with_equals_sign():
    """
    Test that property values containing '=' are correctly parsed and set in Artifactory.
    Regression test for https://github.com/conan-io/conan-extensions/issues/228
    """
    # Configure Artifactory server (credentials stored securely, not printed in logs)
    run(f'conan art:server add artifactory {os.getenv("ART_URL")} '
        f'--user="{os.getenv("CONAN_LOGIN_USERNAME_EXTENSIONS_STG")}" '
        f'--password="{os.getenv("CONAN_PASSWORD_EXTENSIONS_STG")}"')

    # Create and upload a package
    run("conan new cmake_lib -d name=mypkg -d version=1.0 --force")
    run("conan create . -tf=''")
    run("conan upload mypkg/1.0 -c -r extensions-stg")

    # Set a property with '=' in the value (the bug would truncate the value)
    url_with_equals = "https://my.domain/build?id=12345"
    run(f'conan art:property set extensions-stg mypkg/1.0 '
        f'--property="build.url={url_with_equals}" '
        f'--server=artifactory')

    # Verify the property was set correctly by querying Artifactory API
    import urllib.request
    import base64

    art_url = os.getenv("ART_URL")
    art_user = os.getenv("CONAN_LOGIN_USERNAME_EXTENSIONS_STG")
    art_password = os.getenv("CONAN_PASSWORD_EXTENSIONS_STG")

    credentials = base64.b64encode(f"{art_user}:{art_password}".encode()).decode()
    request = urllib.request.Request(
        f"{art_url}/api/storage/extensions-stg/_/mypkg/1.0/_?properties",
        headers={"Authorization": f"Basic {credentials}"}
    )
    response = urllib.request.urlopen(request)
    properties = json.loads(response.read().decode()).get("properties", {})

    # Check that the full URL with '=' is preserved
    assert "build.url" in properties, "Property 'build.url' not found"
    actual_value = properties["build.url"][0]
    assert actual_value == url_with_equals, \
        f"Property value was truncated! Expected '{url_with_equals}', got '{actual_value}'"


@pytest.mark.requires_credentials
def test_append_local_build_info():
    """
    Test that we can append local build infos (without uploding them previously to artifactory)
    """
    build_name = "my_build"
    build_number = "1"

    run("conan new cmake_lib -d name=mypkg -d version=1.0 --force")

    # Create release packages & build info
    run("conan create . --format json -s build_type=Release > create_release.json")
    run("conan upload mypkg/1.0 -c -r extensions-stg")
    run(f"conan art:build-info create create_release.json {build_name}_release {build_number} extensions-stg > {build_name}_release.json")
    bi_data = json.loads(load(f"{build_name}_release.json"))
    assert len(bi_data["modules"]) == 2

    # Create debug packages & build info
    run("conan create . --format json -s build_type=Debug > create_debug.json")
    run("conan upload mypkg/1.0 -c -r extensions-stg")
    run(f"conan art:build-info create create_debug.json {build_name}_debug {build_number} extensions-stg > {build_name}_debug.json")
    bi_data = json.loads(load(f"{build_name}_debug.json"))
    assert len(bi_data["modules"]) == 2

    # Aggregate the release and debug build infos into a new one
    output = run(f"conan art:build-info append {build_name} {build_number} --build-info-file={build_name}_release.json "
                 f"--build-info-file={build_name}_debug.json")
    bi_data = json.loads(output)

    assert bi_data["name"] == build_name
    assert bi_data["number"] == build_number
    assert len(bi_data["modules"]) == 3

    assert bi_data["modules"][0]["id"] == "mypkg/1.0#294e801a0e1da10084441487e95b80e8"
    recipe_files = {artifact["name"] for artifact in bi_data["modules"][0]["artifacts"]}
    assert set(recipe_files) == {"conanfile.py", "conan_sources.tgz", "conanmanifest.txt"}

    for n in [1, 2]:
        # omit pkgid for multi-platform testing
        assert "mypkg/1.0#294e801a0e1da10084441487e95b80e8:" in bi_data["modules"][n]["id"]
        package_files = {artifact["name"] for artifact in bi_data["modules"][n]["artifacts"]}
        assert set(package_files) == {"conanmanifest.txt", "conaninfo.txt", "conan_package.tgz"}
