from ramp_udp.protocol.packet import Packet
from ramp_udp.protocol.serializer import PacketSerializer
from ramp_udp.transport.socket_manager import SocketManager


class UDPSender:
    def __init__(self, host: str, port: int):
        self.socket_manager = SocketManager(host, port)

    def send(self, packet: Packet, destination: tuple[str, int]) -> None:
        data = PacketSerializer.serialize(packet)
        self.socket_manager.send(data, destination)

    def close(self) -> None:
        self.socket_manager.close()

    def receive(self):
        return self.socket_manager.receive()

    def set_timeout(self, timeout: float) -> None:
        self.socket_manager.set_timeout(timeout)