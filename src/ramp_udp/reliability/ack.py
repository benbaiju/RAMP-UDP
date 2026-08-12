from ramp_udp.protocol.message_types import MessageType
from ramp_udp.protocol.packet import Packet


class AckManager:
    @staticmethod
    def create(sequence_number: int) -> Packet:
        return Packet(
            message_type=MessageType.ACK,
            sequence_number=sequence_number,
        )

    @staticmethod
    def is_ack(packet: Packet) -> bool:
        return packet.message_type == MessageType.ACK

    @staticmethod
    def is_valid(packet: Packet, sequence_number: int) -> bool:
        return (
            AckManager.is_ack(packet)
            and packet.sequence_number == sequence_number
        )