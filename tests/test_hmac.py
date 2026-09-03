import threading
from unittest.mock import MagicMock

from ramp_udp.protocol.message_types import MessageType
from ramp_udp.protocol.packet import Packet
from ramp_udp.protocol.serializer import PacketSerializer
from ramp_udp.reliability.ack import AckManager
from ramp_udp.reliability.reliable_receiver import ReliableReceiver
from ramp_udp.reliability.reliable_sender import ReliableSender
from ramp_udp.security.hmac_auth import generate_hmac, verify_hmac


TEST_KEY = b"test-secret-key"


def test_correct_key_and_data_verify():
	data = b"authenticated data"
	tag = generate_hmac(data, TEST_KEY)

	assert verify_hmac(data, tag, TEST_KEY) is True


def test_modified_data_fails_verification():
	tag = generate_hmac(b"original", TEST_KEY)

	assert verify_hmac(b"modified", tag, TEST_KEY) is False


def test_wrong_key_fails_verification():
	data = b"authenticated data"
	tag = generate_hmac(data, TEST_KEY)

	assert verify_hmac(data, tag, b"wrong-key") is False


def test_modified_hmac_fails_verification():
	data = b"authenticated data"
	tag = generate_hmac(data, TEST_KEY)
	modified_tag = bytes([tag[0] ^ 1]) + tag[1:]

	assert verify_hmac(data, modified_tag, TEST_KEY) is False


def test_authenticated_packet_round_trip():
	packet = Packet(
		message_type=MessageType.DATA,
		sequence_number=7,
		payload=b"hello",
	)
	packet.authentication_tag = generate_hmac(
		PacketSerializer.authentication_data(packet), TEST_KEY
	)

	serialized = PacketSerializer.serialize(packet)
	restored = PacketSerializer.deserialize(serialized)

	assert restored == packet
	assert len(restored.authentication_tag) == 32
	assert verify_hmac(
		PacketSerializer.authentication_data(restored),
		restored.authentication_tag,
		TEST_KEY,
	) is True


def test_forged_ack_is_not_accepted():
	ack = AckManager.create(1)
	ack.authentication_tag = generate_hmac(
		PacketSerializer.authentication_data(ack), b"different-key"
	)
	mock_transport = MagicMock()
	mock_transport.receive.side_effect = [
		(PacketSerializer.serialize(ack), ("127.0.0.1", 1)),
		TimeoutError,
	]
	sender = ReliableSender("127.0.0.1", 0)
	sender.sender = mock_transport

	try:
		assert sender._wait_for_ack(1) is False
	finally:
		sender.close()


def test_authenticated_data_communication():
	receiver = ReliableReceiver("127.0.0.1", 0)
	receiver_port = receiver.receiver.socket_manager._socket.getsockname()[1]
	received = []

	def receive_once():
		received.append(receiver.receive())

	thread = threading.Thread(target=receive_once)
	thread.start()
	sender = ReliableSender("127.0.0.1", 0)

	try:
		assert sender.send(b"authenticated message", ("127.0.0.1", receiver_port))
		thread.join(timeout=2)
		assert len(received) == 1
		assert received[0].payload == b"authenticated message"
	finally:
		sender.close()
		receiver.close()
