from ramp_udp.protocol.message_types import MessageType
from ramp_udp.protocol.packet import Packet
from ramp_udp.reliability.ack import AckManager
from ramp_udp.reliability.duplicate import DuplicateDetector
from ramp_udp.transport.udp_receiver import UDPReceiver
from ramp_udp.transport.udp_sender import UDPSender


class ReliableReceiver:
    def __init__(self, host: str, port: int):
        self.receiver = UDPReceiver(host, port)
        self.sender = UDPSender(host, port)
        self.duplicate_detector = DuplicateDetector()

    def receive(self) -> Packet:
        while True:
            packet, address = self.receiver.receive()

            if packet.message_type != MessageType.DATA:
                return packet

            ack = AckManager.create(packet.sequence_number)
            self.sender.send(ack, address)

            if self.duplicate_detector.is_duplicate(packet.sequence_number):
                print(
                    f"Duplicate DATA sequence={packet.sequence_number} "
                    f"(ACK resent, not delivered)"
                )
                continue

            self.duplicate_detector.mark_delivered(packet.sequence_number)
            print(f"Delivering DATA sequence={packet.sequence_number}")
            return packet

    def close(self) -> None:
        self.receiver.close()
        self.sender.close()
