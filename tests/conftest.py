import os
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
