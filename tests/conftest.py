import os
import sys

import pytest


def pytest_collection_modifyitems(items):
    for item in items:
        if "requires_credentials" in item.keywords:
            for env in ["CONAN_LOGIN_USERNAME_EXTENSIONS_PROD", "CONAN_PASSWORD_EXTENSIONS_PROD",
                        "CONAN_LOGIN_USERNAME_EXTENSIONS_STG", "CONAN_PASSWORD_EXTENSIONS_STG",
                        "ART_URL"]:
                if not os.getenv(env):
                    item.add_marker(pytest.mark.skip(reason=f"Missing required credentials environment variable {env}."))
                    print(f"Skipping test {item.nodeid}. Missing required credentials environment variable {env}")
                    break

ALL_OS = set("darwin linux win32".split())


def pytest_runtest_setup(item):
    supported_platforms = ALL_OS.intersection(mark.name for mark in item.iter_markers())
    plat = sys.platform
    if supported_platforms and plat not in supported_platforms:
        pytest.skip("cannot run on platform {}".format(plat))
