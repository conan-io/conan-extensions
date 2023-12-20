import requests


STATUSPAGE_URL = "https://api.statuspage.io/v1"


def post(url, token, json, verify) -> dict:
    """
    POST request to Status Page API.
    """
    return _request(url, token, json, verify, requests.post)


def patch(url, token, json, verify) -> dict:
    """
    PATCH request to Status Page API.
    """
    return _request(url, token, json, verify, requests.patch)


def _request(url, token, json, verify, method) -> dict:
    """
    Generic request to Status Page API.
    """
    url = f"{STATUSPAGE_URL}/{url}"
    headers = {"Authorization": f"OAuth {token}", "Content-Type": "application/json"}
    response = method(url, json=json, headers=headers, verify=verify)
    response.raise_for_status()
    return response.json()
