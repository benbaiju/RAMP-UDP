import struct

from ramp_udp.protocol.constants import (
    HEADER_SIZE,
    HMAC_SIZE,
    MAGIC_NUMBER,
    MAX_PAYLOAD_SIZE,
    PROTOCOL_VERSION,
)
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
        if len(packet.payload) > MAX_PAYLOAD_SIZE:
            raise ValueError("Payload exceeds the maximum size.")
        if len(packet.authentication_tag) not in (0, HMAC_SIZE):
            raise ValueError("Invalid authentication tag length.")
        return cls.authentication_data(packet) + packet.authentication_tag

    @classmethod
    def deserialize(cls, data: bytes) -> Packet:
        if len(data) < HEADER_SIZE:
            raise ValueError("Packet is smaller than the header size.")

        magic, version, message_type, sequence_number, payload_length = struct.unpack(
            cls.HEADER_FORMAT,
            data[:HEADER_SIZE],
        )

        if magic != MAGIC_NUMBER:
            raise ValueError("Invalid protocol magic number.")
        if version != PROTOCOL_VERSION:
            raise ValueError("Unsupported protocol version.")
        if payload_length > MAX_PAYLOAD_SIZE:
            raise ValueError("Payload exceeds the maximum size.")

        expected_length = HEADER_SIZE + payload_length
        if len(data) < expected_length:
            raise ValueError("Packet payload is truncated.")

        payload = data[HEADER_SIZE:expected_length]
        remaining = data[expected_length:]
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