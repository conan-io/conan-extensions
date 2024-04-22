import os
import sys

import pytest


def pytest_collection_modifyitems(items):
    for item in items:
        if "requires_credentials" in item.keywords:
            if (
                not os.getenv("CONAN_LOGIN_USERNAME_EXTENSIONS_PROD")
                or not os.getenv("CONAN_PASSWORD_EXTENSIONS_PROD")
                or not os.getenv("CONAN_LOGIN_USERNAME_EXTENSIONS_STG")
                or not os.getenv("CONAN_PASSWORD_EXTENSIONS_STG")
                or not os.getenv("ART_URL")
            ):
                item.add_marker(pytest.mark.skip(reason="Missing required credentials environment variables"))
                print(f"Skipping test {item.nodeid}. Missing required credentials environment variables.")

ALL_OS = set("darwin linux win".split())


def pytest_runtest_setup(item):
    supported_platforms = ALL_OS.intersection(mark.name for mark in item.iter_markers())
    plat = sys.platform
    if supported_platforms and plat not in supported_platforms:
        pytest.skip("cannot run on platform {}".format(plat))
