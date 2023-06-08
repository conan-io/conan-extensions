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
