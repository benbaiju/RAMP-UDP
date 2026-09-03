import pytest
from unittest.mock import MagicMock, patch

from ramp_udp.protocol.constants import HEADER_SIZE, HMAC_SIZE, MAGIC_NUMBER
from ramp_udp.protocol.message_types import MessageType
from ramp_udp.protocol.packet import Packet
from ramp_udp.protocol.serializer import PacketSerializer
from ramp_udp.transport.udp_receiver import UDPReceiver


def test_authenticated_packet_round_trip_preserves_tag():
	packet = Packet(MessageType.DATA, 4, b"hello", b"x" * HMAC_SIZE)

	restored = PacketSerializer.deserialize(PacketSerializer.serialize(packet))

	assert restored == packet


def test_invalid_magic_is_rejected():
	packet = Packet(MessageType.DATA, 1, b"data")
	data = bytearray(PacketSerializer.serialize(packet))
	data[0:2] = b"XX"

	with pytest.raises(ValueError, match="magic"):
		PacketSerializer.deserialize(data)


def test_invalid_version_is_rejected():
	packet = Packet(MessageType.DATA, 1, b"data")
	data = bytearray(PacketSerializer.serialize(packet))
	data[2] = 99

	with pytest.raises(ValueError, match="version"):
		PacketSerializer.deserialize(data)


def test_truncated_payload_is_rejected():
	packet = Packet(MessageType.DATA, 1, b"data")

	with pytest.raises(ValueError, match="truncated"):
		PacketSerializer.deserialize(PacketSerializer.serialize(packet)[:-1])


def test_trailing_bytes_are_rejected():
	packet = Packet(MessageType.DATA, 1, b"data")

	with pytest.raises(ValueError, match="authentication tag"):
		PacketSerializer.deserialize(PacketSerializer.serialize(packet) + b"x")


def test_payload_limit_is_enforced():
	packet = Packet(MessageType.DATA, 1, b"x" * 1025)

	with pytest.raises(ValueError, match="maximum"):
		PacketSerializer.serialize(packet)


def test_udp_receiver_skips_malformed_datagram():
	valid_packet = Packet(MessageType.DATA, 1, b"valid")
	socket_manager = MagicMock()
	socket_manager.receive.side_effect = [
		(b"bad", ("127.0.0.1", 1)),
		(PacketSerializer.serialize(valid_packet), ("127.0.0.1", 1)),
	]

	with patch(
		"ramp_udp.transport.udp_receiver.SocketManager",
		return_value=socket_manager,
	):
		receiver = UDPReceiver("127.0.0.1", 1)
		packet, _ = receiver.receive()
		receiver.close()

	assert packet == valid_packet
