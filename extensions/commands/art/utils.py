import json
import requests

from conan.errors import ConanException


def load_json(json_file):
    try:
        with open(json_file, 'r') as f:
            data = json.load(f)
        return data
    except FileNotFoundError:
        raise ConanException(f"Error: The file {json_file} was not found.")
    except json.JSONDecodeError:
        raise ConanException(f"Error: The file {json_file} is not a valid JSON file.")
    except Exception as e:
        raise ConanException(f"An unexpected error occurred: {e}")

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

class UnauthorizedException(ConanException):
    """Exception raised for unauthorized request (HTTP 401)."""
    pass

class ForbiddenException(ConanException):
    """Exception raised for forbidden request (HTTP 403)."""
    pass

class NotFoundException(ConanException):
    """Exception raised for request to non-existent resources (HTTP 404)."""
    pass

class BadRequestException(ConanException):
    """Exception raised for bad request (HTTP 400)."""
    pass

class UnexpectedResponseException(ConanException):
    """Exception raised for unexpected response status codes."""
    pass


def api_request(method, request_url, user=None, password=None, json_data=None,
                sign_key_name=None, plain_data=None):
    headers = {}
    if json_data and plain_data:
        raise ConanException("Cannot send both json and plain data in the same request")
    if json_data:
        headers.update({"Content-Type": "application/json"})
    if plain_data:
        headers.update({"Content-Type": "text/plain"})
    if sign_key_name:
        headers.update({"X-JFrog-Crypto-Key-Name": sign_key_name})

    requests_method = getattr(requests, method)
    if user and password:
        response = requests_method(request_url, auth=(
            user, password), data=json_data or plain_data, headers=headers)
    else:
        response = requests_method(request_url)

    if response.status_code == 400:
        raise BadRequestException(response_to_str(response))
    elif response.status_code == 401:
        raise UnauthorizedException(response_to_str(response))
    elif response.status_code == 403:
        raise ForbiddenException(response_to_str(response))
    elif response.status_code == 404:
        raise NotFoundException(response_to_str(response))
    elif response.status_code not in [200, 204]:
        raise UnexpectedResponseException(response_to_str(response))

    return response_to_str(response)


def assert_server_or_url_user_password(args):
    if args.server and args.url:
        raise ConanException("--server and --url (with --user & --password/--token)) flags cannot be used together.")
    if not args.server and not args.url:
        raise ConanException("Specify --server or --url (with --user & --password/--token) flags to contact Artifactory.")
    if args.url:
        if not (args.user and (args.password or args.token)):
            raise ConanException("Specify --user and --password/--token to use with the --url flag to contact Artifactory.")
        if args.password and args.token:
            raise ConanException("--password and --token arguments cannot be used at the same time. Please specify either --password OR --token.")
    assert args.server or (args.url and args.user and (args.password or args.token))
