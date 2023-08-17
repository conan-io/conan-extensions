import subprocess


def run(cmd, error=False, *, stdout=subprocess.PIPE, stderr=subprocess.PIPE):
    process = subprocess.Popen(cmd, 
                               stdout=stdout,
                               stderr=stderr,
                               shell=True)

    out, err = process.communicate()
    out = out.decode("utf-8") if stdout else ""
    err = err.decode("utf-8") if stderr else ""
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
