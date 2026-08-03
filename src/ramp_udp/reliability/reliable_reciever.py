from ramp_udp.protocol.message_types import MessageType
from ramp_udp.protocol.packet import Packet
from ramp_udp.reliability.ack import AckManager
from ramp_udp.transport.receiver import Receiver
from ramp_udp.transport.sender import Sender


class ReliableReceiver:
    def __init__(self, host: str, port: int):
        self.receiver = Receiver(host, port)
        self.sender = Sender(host, port)

    def receive(self) -> Packet:
        packet, address = self.receiver.receive()

        if packet.message_type == MessageType.DATA:
            ack = AckManager.create(packet.sequence_number)
            self.sender.send(ack, address)

        return packet

    def close(self) -> None:
        self.receiver.close()
        self.sender.close()