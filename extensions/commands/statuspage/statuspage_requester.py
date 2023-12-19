import requests


class Requester:

    STATUSPAGE_URL = "https://api.statuspage.io/v1"

    def post(self, url, token, json, verify) -> dict:
        url = f"{Requester.STATUSPAGE_URL}/{url}"
        headers = {"Authorization": f"OAuth {token}", "Content-Type": "application/json"}
        response = requests.post(url, json=json, headers=headers, verify=verify)
        response.raise_for_status()
        return response.json()

    def patch(self, url, token, json, verify) -> dict:
        url = f"{Requester.STATUSPAGE_URL}/{url}"
        headers = {"Authorization": f"OAuth {token}", "Content-Type": "application/json"}
        response = requests.patch(url, json=json, headers=headers, verify=verify)
        response.raise_for_status()
        return response.json()
