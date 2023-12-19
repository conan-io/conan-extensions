import requests



STATUSPAGE_URL = "https://api.statuspage.io/v1"

def post(url, token, json, verify) -> dict:
    url = f"{STATUSPAGE_URL}/{url}"
    headers = {"Authorization": f"OAuth {token}", "Content-Type": "application/json"}
    response = requests.post(url, json=json, headers=headers, verify=verify)
    response.raise_for_status()
    return response.json()

def patch(url, token, json, verify) -> dict:
    url = f"{STATUSPAGE_URL}/{url}"
    headers = {"Authorization": f"OAuth {token}", "Content-Type": "application/json"}
    response = requests.patch(url, json=json, headers=headers, verify=verify)
    response.raise_for_status()
    return response.json()
