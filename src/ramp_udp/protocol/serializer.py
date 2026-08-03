import struct

from ramp_udp.protocol.constants import HEADER_SIZE
from ramp_udp.protocol.message_types import MessageType
from ramp_udp.protocol.packet import Packet


class PacketSerializer:
    HEADER_FORMAT = "!2sBBIH"

    @classmethod
    def serialize(cls, packet: Packet) -> bytes:
        header = struct.pack(
            cls.HEADER_FORMAT,
            packet.magic,
            packet.version,
            packet.message_type.value,
            packet.sequence_number,
            packet.payload_length,
        )

        return header + packet.payload

    @classmethod
    def deserialize(cls, data: bytes) -> Packet:
        if len(data) < HEADER_SIZE:
            raise ValueError("Packet is smaller than the header size.")

        magic, version, message_type, sequence_number, payload_length = struct.unpack(
            cls.HEADER_FORMAT,
            data[:HEADER_SIZE],
        )

        payload = data[HEADER_SIZE : HEADER_SIZE + payload_length]

        return Packet(
            magic=magic,
            version=version,
            message_type=MessageType(message_type),
            sequence_number=sequence_number,
            payload=payload,
        )