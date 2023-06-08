import json
import requests

from conan.errors import ConanException


def response_to_str(response):
    content = response.content
    try:
        # A bytes message, decode it as str
        if isinstance(content, bytes):
            content = content.decode('utf-8')

        content_type = response.headers.get("content-type")

        if content_type == "application/json":
            # Errors from Artifactory looks like:
            #  {"errors" : [ {"status" : 400, "message" : "Bla bla bla"}]}
            try:
                data = json.loads(content)["errors"][0]
                content = "{}: {}".format(data["status"], data["message"])
            except Exception:
                pass
        elif "text/html" in content_type:
            content = "{}: {}".format(response.status_code, response.reason)

        return content
    except Exception:
        return response.content


def api_request(method, request_url, user=None, password=None, json_data=None,
                sign_key_name=None):
    headers = {}
    if json_data:
        headers.update({"Content-Type": "application/json"})
    if sign_key_name:
        headers.update({"X-JFrog-Crypto-Key-Name": sign_key_name})

    requests_method = getattr(requests, method)
    if user and password:
        response = requests_method(request_url, auth=(
            user, password), data=json_data, headers=headers)
    else:
        response = requests_method(request_url)

    if response.status_code == 401:
        raise Exception(response_to_str(response))
    elif response.status_code not in [200, 204]:
        raise Exception(response_to_str(response))

    return response_to_str(response)


def assert_server_or_url_user_password(args):
    if args.server and args.url:
        raise ConanException("--server and --url (with --user & --password) flags cannot be used together.")
    if not args.server and not args.url:
        raise ConanException("Specify --server or --url (with --user & --password) flags to contact Artifactory.")
    if args.url:
        if not args.user or not args.password:
            raise ConanException("Specify --user and --password to use with the --url flag to contact Artifactory.")
    assert args.server or (args.url and args.user and args.password)
