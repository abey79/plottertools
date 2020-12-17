import logging
import socketserver
from typing import Optional

import click
from serial import Serial

SERIAL_DEVICE: Optional[Serial] = None

logging.getLogger().setLevel(logging.INFO)


class MyTCPHandler(socketserver.StreamRequestHandler):
    """
    This class works similar to the TCP handler class, except that
    self.request consists of a pair of data and client socket, and since
    there is no connection the client address must be given explicitly
    when sending data back via sendto().
    """

    def handle(self):
        data = self.rfile.read()
        logging.info(f"writing {len(data)} bytes")
        SERIAL_DEVICE.write(data)
        logging.info(f"done")


@click.command()
@click.argument("device", type=str)
@click.option("--address", "-a", type=str, default="localhost", help="server address")
@click.option("--port", "-p", type=int, default="5678", help="server port")
@click.option("--rtscts", "-r", is_flag=True, help="enable hardware flow control")
def serialserver(device: str, address: str, port: int, rtscts: bool):
    global SERIAL_DEVICE
    SERIAL_DEVICE = Serial(port=device, rtscts=rtscts)
    with socketserver.TCPServer((address, port), MyTCPHandler) as server:
        server.serve_forever()
