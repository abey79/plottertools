"""
Test for existence:

    # 0 if exists, 1 if not
    screen -S SCREEN_NAME -Q select

Create w/o attaching:

    screen -mdS "test"
"""
import logging
import os
import shlex
import sys

import fabric
import toml

SCREEN_NAME = "raxicli"


def execute_command(connection, cmd: str) -> int:
    logging.info(f"executing: {cmd}")
    res = connection.run(cmd, warn=True)
    return res.exited


def check_screen_exists(connection):
    res = execute_command(connection, f"screen -S {SCREEN_NAME} -Q select > /dev/null")
    if res == 1:
        logging.info("Screen not found, creating one...")
        if execute_command(connection, f"screen -mdS {SCREEN_NAME}") != 0:
            raise RuntimeError("screen could not be created")
    else:
        send_command(
            connection, ""
        )  # somehow needed for the next command to be executed
        logging.info("Screen found.")


def send_command(connection, cmd: str):
    execute_command(connection, f"screen -S {SCREEN_NAME} -X stuff '" + cmd + r"\r'")


def main():
    path = os.path.expanduser("~/.plottertools.toml")
    if not os.path.exists(path):
        print("!!! Config file not found", file=sys.stderr)
    config = toml.load(str(path))

    hostname = config["raxicli"]["hostname"]
    axicli_path = config["raxicli"]["axicli_path"]
    svg_dir_path = config["raxicli"]["svg_dir_path"]

    connection = fabric.Connection(hostname)

    check_screen_exists(connection)

    for i, arg in enumerate(sys.argv):
        if arg.endswith(".svg") and os.path.exists(arg):
            connection.put(arg, remote=svg_dir_path)
            sys.argv[i] = svg_dir_path + os.path.basename(arg)

    if len(sys.argv) > 1:
        send_command(connection, axicli_path + " " + shlex.join(sys.argv[1:]))


if __name__ == "__main__":
    main()
