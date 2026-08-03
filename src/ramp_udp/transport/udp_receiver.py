from ramp_udp.protocol.packet import Packet
from ramp_udp.protocol.serializer import PacketSerializer
from ramp_udp.transport.socket_manager import SocketManager


class UDPReceiver:
    def __init__(self, host: str, port: int):
        self.socket_manager = SocketManager(host, port)
        self.socket_manager.bind()

    def receive(self) -> tuple[Packet, tuple[str, int]]:
        data, address = self.socket_manager.receive()
        packet = PacketSerializer.deserialize(data)
        return packet, address

    def close(self) -> None:
        self.socket_manager.close()