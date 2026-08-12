import socket

from ramp_udp.protocol.constants import BUFFER_SIZE

class SocketManager:
    def __init__(self, host: str, port: int):
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.host = host
        self.port = port

    def bind(self) -> None:
        self._socket.bind((self.host, self.port))

    def send(self, data: bytes, address: tuple[str, int]) -> None:
        self._socket.sendto(data, address)

    def receive(self) -> tuple[bytes, tuple[str, int]]:
        return self._socket.recvfrom(BUFFER_SIZE)

    def set_timeout(self, timeout: float) -> None:
        self._socket.settimeout(timeout)

    def close(self) -> None:
        self._socket.close()