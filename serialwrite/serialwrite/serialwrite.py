import logging
import socket
from typing import BinaryIO

import click
from serial import Serial
from tqdm import tqdm

logging.getLogger().setLevel(logging.INFO)


@click.command()
@click.argument("file", type=click.File("rb"))
@click.argument("dest", type=str)
@click.option("--remote", "-r", is_flag=True, help="send data to a remote serialserver")
@click.option("--port", "-p", type=int, default="5678", help="server port")
@click.option("--rtscts", "-hw", is_flag=True, help="enable hardware flow control")
def serialwrite(
    file: BinaryIO, dest: str, remote: bool, port: int, rtscts: bool
) -> None:
    data = file.read()
    if remote:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            # Connect to server and send data
            sock.connect((dest, port))
            sock.sendall(data)
    else:
        serial = Serial(port=dest, rtscts=rtscts)
        # serial.write(data)
        for c in tqdm(data):
            serial.write(c)
        logging.info("Flushing...")
        serial.flush()
        serial.close()
