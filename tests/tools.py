import subprocess
import time


def run(cmd, error=False, *, stdout=subprocess.PIPE, stderr=subprocess.STDOUT):
    print("Running: {}".format(cmd))
    start_time = time.time()

    process = subprocess.Popen(cmd, stdout=stdout, stderr=stderr, shell=True, text=True)

    output = ''
    
    for line in iter(process.stdout.readline, ''):
        print(line, end='', flush=True)
        output += line

    ret = process.wait()
    end_time = time.time()
    
    elapsed_time = end_time - start_time
    print(f"Elapsed time: {elapsed_time:.2f} seconds")

    if ret != 0 and not error:
        raise Exception(f"Failed cmd: {cmd}\n{output}")
    if ret == 0 and error:
        raise Exception(f"Cmd succeeded (failure expected): {cmd}\n{output}")

    return output


def save(f, content):
    with open(f, "w") as f:
        f.write(content)


def load(f):
    with open(f, "r") as f:
        return f.read()
