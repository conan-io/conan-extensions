import os
import tempfile
import json
import platform

import pytest

from tools import run


@pytest.fixture(autouse=True)
def conan_test():
    old_env = dict(os.environ)
    env_vars = {'CONAN_HOME': tempfile.mkdtemp(suffix='conans')}
    os.environ.update(env_vars)
    current = tempfile.mkdtemp(suffix='conans')
    cwd = os.getcwd()
    os.chdir(current)
    try:
        yield
    finally:
        os.chdir(cwd)
        os.environ.clear()
        os.environ.update(old_env)


@pytest.mark.win32
def test_copy_pdb_hook():
    repo = os.path.join(os.path.dirname(__file__), "..")
    run(f'conan config install {repo}')
    conan_home = run('conan config home').strip()
    hooks_path = os.path.join(conan_home, 'extensions', 'hooks')
    old_file = os.path.join(hooks_path, '_hook_copy_pdbs_to_package.py')
    new_file = os.path.join(hooks_path, 'hook_copy_pdbs_to_package.py')
    os.rename(old_file, new_file)
    run('conan profile detect')
    run('conan new cmake_lib -d name=lib -d version=1.0')
    out = run('conan create . -s build_type=Debug -o "*:shared=True" -tf=""')
    assert "PDBs post package hook running" in out
    list_output = run('conan list lib/1.0:* --format=json')
    list_json = json.loads(list_output)
    revision = list_json['Local Cache']['lib/1.0']['revisions'].values()
    revision_info = next(iter(revision))
    package_id = next(iter(revision_info['packages']))
    path = run(fr'conan cache path lib/1.0:{package_id}').strip()
    assert os.path.isfile(os.path.join(path, 'bin', 'lib.pdb'))
