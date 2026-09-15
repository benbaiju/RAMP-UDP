from ramp_udp.protocol.packet import Packet
from ramp_udp.protocol.serializer import PacketSerializer
from ramp_udp.transport.socket_manager import SocketManager


class UDPSender:
    def __init__(
        self,
        host: str,
        port: int,
        socket_manager: SocketManager | None = None,
    ):
        self._owns_socket = socket_manager is None
        self.socket_manager = socket_manager or SocketManager(host, port)
        if self._owns_socket:
            self.socket_manager.bind()

    def send(self, packet: Packet, destination: tuple[str, int]) -> None:
        data = PacketSerializer.serialize(packet)
        self.socket_manager.send(data, destination)

    def close(self) -> None:
        if self._owns_socket:
            self.socket_manager.close()

    def receive(self):
        return self.socket_manager.receive()

    def set_timeout(self, timeout: float) -> None:
        self.socket_manager.set_timeout(timeout)