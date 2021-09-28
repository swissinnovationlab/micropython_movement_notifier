#!/usr/bin/env python3
import os
import sys
import select
import pty
from subprocess import Popen
from time import time, sleep
import typer
import glob

options = {
    "DEVICE_PATH": "/dev/ttyACM0",
    "BUFFER_SIZE": 512,
    "VERBOSE": False
}


class Base:
    # Foreground:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    # Formatting
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    # End colored text
    END = '\033[0m'
    NC = '\x1b[0m'  # No Color


def run_bash_cmd(cmd, echo=False, interaction={}, return_lines=True, return_code=False, cr_as_newline=False):
    if options["VERBOSE"]:
        echo = True
    if echo:
        print("CMD:", cmd)
    master_fd, slave_fd = pty.openpty()
    line = ""
    lines = []
    with Popen(cmd, shell=True, preexec_fn=os.setsid, stdin=slave_fd, stdout=slave_fd, stderr=slave_fd, universal_newlines=True) as p:
        while p.poll() is None:
            r, w, e = select.select([sys.stdin, master_fd], [], [], 0.01)
            if master_fd in r:
                o = os.read(master_fd, 10240).decode("UTF-8")
                if o:
                    for c in o:
                        if cr_as_newline and c == "\r":
                            c = "\n"
                        if c == "\n":
                            if line and line not in interaction.values():
                                clean = line.strip().split('\r')[-1]
                                lines.append(clean)
                                if echo:
                                    print("STD:", line)
                            line = ""
                        else:
                            line += c
            if line:  # pass password to prompt
                for key in interaction:
                    if key in line:
                        if echo:
                            print("PMT:", line)
                        os.write(master_fd, ("%s" % (interaction[key])).encode())
                        os.write(master_fd, "\r\n".encode())
                        line = ""
        if line:
            clean = line.strip().split('\r')[-1]
            lines.append(clean)

    os.close(master_fd)
    os.close(slave_fd)

    if return_lines and return_code:
        return lines, p.returncode
    elif return_code:
        return p.returncode
    else:
        return lines


def dismember(it, num=3):
    it = iter(it)
    while it.__length_hint__() > 0:
        if (it.__length_hint__() >= num):
            yield [next(it) for i in range(num)]
        else:
            yield [next(it) for i in range(it.__length_hint__())]


def get_rshell_base_command():
    return "rshell -p %s --buffer-size %d" % (options["DEVICE_PATH"], options["BUFFER_SIZE"])


def get_mpremote_base_command():
    return "mpremote"


app = typer.Typer(help="Awesome CLI micropython.")


@app.command()
def repl():
    cmd = "%s repl" % (get_rshell_base_command())
    os.system(cmd)


@app.command()
def shell():
    cmd = "%s" % (get_rshell_base_command())
    os.system(cmd)


@app.command()
def sync():
    cmd = "%s rsync ./src /pyboard/" % (get_rshell_base_command())
    lines = run_bash_cmd(cmd)
    for line in lines:
        if "timed out or error" in line:
            print("Error trying to fix the issue")
            rm_empty()
            cmd = "%s rsync ./src /pyboard/" % (get_rshell_base_command())
            lines = run_bash_cmd(cmd)
            for line in lines:
                if "timed out or error" in line:
                    print("%sERROR:%s while flashing" % (Base.WARNING, Base.END))


@app.command()
def _cp(file):
    cmd = "%s cp %s /pyboard/" % (get_rshell_base_command(), file)
    lines = run_bash_cmd(cmd)
    for line in lines:
        if "timed out or error" in line:
            print("%sERROR:%s while flashing" % (Base.WARNING, Base.END))
            return False
    return True


@app.command()
def cp():
    files = glob.glob("./src/*.py")
    files.sort()
    if len(files):
        for e, f in enumerate(files):
            print("[%d] %s" % (e, f.split("/")[2]))
        index = int(input("Select index: "))
        _cp(files[index])


@app.command()
def _rm(file):
    cmd = "%s fs rm :%s" % (get_mpremote_base_command(), file)
    lines = run_bash_cmd(cmd)
    for line in lines:
        if "Traceback" in line:
            print("%sERROR:%s while flashing" % (Base.WARNING, Base.END))
            return False
    return True


@app.command()
def rm():
    cmd = "%s fs ls" % (get_mpremote_base_command())
    files = [line.strip().split(" ")[1] for line in run_bash_cmd(cmd)][1:]
    files.sort()
    if len(files):
        for e, f in enumerate(files):
            print("[%d] %s" % (e, f))
        index = int(input("Select index: "))
        _rm(files[index])


@app.command()
def cp_all():
    files = glob.glob("./src/*.py")
    for file in files:
        if not _cp(file):
            _rm(file)
            input("restart board and and press Return")
            if not _cp(file):
                print("Can't copy aborting")


@app.command()
def rm_all():
    cmd = "%s fs ls" % (get_mpremote_base_command())
    files = [line.strip().split(" ")[1] for line in run_bash_cmd(cmd)][1:]
    for f in files:
        cmd = "%s fs rm :%s" % (get_mpremote_base_command(), f)
        lines = run_bash_cmd(cmd)
        for line in lines:
            if "Traceback" in line:
                print("%sERROR:%s while flashing" % (Base.WARNING, Base.END))
                return


@app.command()
def rm_empty():
    cmd = "%s fs ls" % (get_mpremote_base_command())
    files = [(line.strip().split(" ")[1], line.strip().split(" ")[0]) for line in run_bash_cmd(cmd)][1:]
    for f in files:
        if f[1] == str(0):
            cmd = "%s fs rm :%s" % (get_mpremote_base_command(), f)
            lines = run_bash_cmd(cmd)
            for line in lines:
                if "Traceback" in line:
                    print("%sERROR:%s while flashing" % (Base.WARNING, Base.END))
                    return


@app.callback()
def main(verbose: bool = True, device_path: str = ""):
    global options
    if verbose:
        options["VERBOSE"] = verbose
    if device_path:
        options["DEVICE_PATH"] = device_path


if __name__ == "__main__":
    app()
