import struct

from ramp_udp.protocol.constants import HEADER_SIZE, HMAC_SIZE
from ramp_udp.protocol.message_types import MessageType
from ramp_udp.protocol.packet import Packet


class PacketSerializer:
    HEADER_FORMAT = "!2sBBIH"

    @classmethod
    def authentication_data(cls, packet: Packet) -> bytes:
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
    def serialize(cls, packet: Packet) -> bytes:
        return cls.authentication_data(packet) + packet.authentication_tag

    @classmethod
    def deserialize(cls, data: bytes) -> Packet:
        if len(data) < HEADER_SIZE:
            raise ValueError("Packet is smaller than the header size.")

        magic, version, message_type, sequence_number, payload_length = struct.unpack(
            cls.HEADER_FORMAT,
            data[:HEADER_SIZE],
        )

        payload = data[HEADER_SIZE : HEADER_SIZE + payload_length]
        remaining = data[HEADER_SIZE + payload_length :]
        if len(remaining) not in (0, HMAC_SIZE):
            raise ValueError("Invalid authentication tag length.")

        return Packet(
            magic=magic,
            version=version,
            message_type=MessageType(message_type),
            sequence_number=sequence_number,
            payload=payload,
            authentication_tag=remaining,
        )