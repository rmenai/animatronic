import logging
import time
from typing import List, Tuple

import serial.tools.list_ports
from pygame import Surface
from serial import Serial

from app.core import constants
from app.state import pool

log = logging.getLogger(__name__)


class Arduino:
    """Represents the arduino board UI."""

    def __init__(self, pos: Tuple[int, int]):
        self.pos = pos
        self.port, self.ports = "", []

        self.serial = None
        self.multiple_ports = False

        self.p = pool.submit(self.try_get_ports)

    def get_ports(self) -> None:
        """Returns the port of the arduino."""
        ports = list(serial.tools.list_ports.comports())
        if not ports:
            self.refresh([])
            return
        elif len(ports) > 1:
            self.multiple_ports = True
            log.warning("Multiple ports found, using the first one")

        self.refresh([port.device for port in ports])

    def refresh(self, ports: List[str]) -> None:
        """Refresh the serial."""
        try:
            # Initialize serial.
            self.serial = Serial(ports[0], constants.audio.baud_rate, timeout=1)
            time.sleep(1)

            self.port = ports[0]
            self.ports = ports
            log.info(f"Connected to arduino board at port {self.port}")
        except KeyError:
            log.debug("No ports found")
            self.serial = None

    def try_get_ports(self) -> None:
        """Try to detect arduino port in a loop."""
        while not self.port:
            self.get_ports()
            time.sleep(3)

        self.p = None

    def update(self) -> None:
        """Updates the handle's angle."""
        pass

    def render(self, screen: Surface) -> None:
        """Renders the handle to the given surface."""
        pass

    def send(self, rotation: int) -> None:
        """Sends the given rotation to the arduino."""
        if not self.port:
            if not self.p or self.p.done():
                self.port, self.ports = "", []
                self.p = pool.submit(self.try_get_ports)
            return

        try:
            self.serial.write(bytes(f"servo,{rotation}\n", "utf-8"))
        except serial.serialutil.SerialException:
            self.serial = None
            self.port, self.ports = "", []
            self.p = pool.submit(self.try_get_ports)

            log.warning("Lost connection to arduino board")
