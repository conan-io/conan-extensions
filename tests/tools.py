import json
import requests
import subprocess


def run(cmd, error=False):
    process = subprocess.Popen(cmd, 
                               stdout=subprocess.PIPE, 
                               stderr=subprocess.PIPE, 
                               shell=True)

    out, err = process.communicate()
    out = out.decode("utf-8")
    err = err.decode("utf-8")
    ret = process.returncode

    output = err + out
    if ret != 0 and not error:
        raise Exception("Failed cmd: {}\n{}".format(cmd, output))
    if ret == 0 and error:
        raise Exception(
            "Cmd succeded (failure expected): {}\n{}".format(cmd, output))
    return output


def save(f, content):
    with open(f, "w") as f:
        f.write(content)


def load(f):
    with open(f, "r") as f:
        return f.read()


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


def create_artifactory_project(url, user, password, project_name, project_key):
    request_url = f"{url}/access/api/v1/projects"
    payload = {
        "display_name": project_name,
        "description": "this is the description",
        "admin_privileges": {
            "manage_members": True,
            "manage_resources": True,
            "manage_security_assets": True,
            "index_resources": True,
            "allow_ignore_rules": True
        },
        "storage_quota_bytes": 0,
        "project_key": project_key
    }
    api_request("post", request_url, user, password, json.dumps(payload))


def delete_artifactory_project(url, user, password, project_key):
    request_url = f"{url}/access/api/v1/projects/{project_key}"
    api_request("delete", request_url, user, password)
