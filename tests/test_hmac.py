import threading
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest

from ramp_udp.protocol.message_types import MessageType
from ramp_udp.protocol.constants import MAX_OUT_OF_ORDER_BUFFER_SIZE
from ramp_udp.protocol.packet import Packet
from ramp_udp.protocol.serializer import PacketSerializer
from ramp_udp.reliability.ack import AckManager
from ramp_udp.reliability.reliable_receiver import ReliableReceiver
from ramp_udp.reliability.reliable_sender import ReliableSender
from ramp_udp.security.hmac_auth import generate_hmac, verify_hmac


TEST_KEY = b"ramp-udp-development-key"


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


def _authenticated_data(sequence_number: int, payload: bytes) -> Packet:
	packet = Packet(
		message_type=MessageType.DATA,
		sequence_number=sequence_number,
		payload=payload,
	)
	packet.authentication_tag = generate_hmac(
		PacketSerializer.authentication_data(packet),
		TEST_KEY,
	)
	return packet


def _mock_receiver(packets):
	receiver_transport = MagicMock()
	receiver_transport.receive.side_effect = [
		(packet, ("127.0.0.1", 1))
		for packet in packets
	]
	sender_transport = MagicMock()
	receiver_patcher = patch(
		"ramp_udp.reliability.reliable_receiver.UDPReceiver",
		return_value=receiver_transport,
	)
	sender_patcher = patch(
		"ramp_udp.reliability.reliable_receiver.UDPSender",
		return_value=sender_transport,
	)
	return receiver_patcher, sender_patcher, receiver_transport, sender_transport


def test_first_expected_data_is_delivered():
	receiver_patcher, sender_patcher, _, _ = _mock_receiver(
		[_authenticated_data(1, b"one")]
	)
	with receiver_patcher, sender_patcher:
		receiver = ReliableReceiver("127.0.0.1", 1)
		assert receiver.receive().payload == b"one"
		assert receiver.next_expected_sequence == 2
		receiver.close()


def test_out_of_order_data_is_buffered_without_delivery_or_ack():
	receiver_patcher, sender_patcher, _, sender_transport = _mock_receiver(
		[_authenticated_data(1, b"one"), _authenticated_data(3, b"three")]
	)
	with receiver_patcher, sender_patcher:
		receiver = ReliableReceiver("127.0.0.1", 1)
		assert receiver.receive().payload == b"one"
		receiver.receiver.receive.side_effect = [
			(_authenticated_data(3, b"three"), ("127.0.0.1", 1)),
			TimeoutError,
		]
		with pytest.raises(TimeoutError):
			receiver.receive()
		assert 3 in receiver._out_of_order
		assert receiver.next_expected_sequence == 2
		assert sender_transport.send.call_count == 1
		receiver.close()


def test_buffered_data_is_delivered_after_missing_sequence():
	packets = [
		_authenticated_data(1, b"one"),
		_authenticated_data(3, b"three"),
		_authenticated_data(2, b"two"),
	]
	receiver_patcher, sender_patcher, _, _ = _mock_receiver(packets)
	with receiver_patcher, sender_patcher:
		receiver = ReliableReceiver("127.0.0.1", 1)
		assert receiver.receive().payload == b"one"
		assert receiver.receive().payload == b"two"
		assert receiver.receive().payload == b"three"
		assert receiver.next_expected_sequence == 4
		receiver.close()


def test_duplicate_delivered_data_is_not_delivered_twice():
	packets = [
		_authenticated_data(1, b"one"),
		_authenticated_data(1, b"one"),
		_authenticated_data(2, b"two"),
	]
	receiver_patcher, sender_patcher, _, _ = _mock_receiver(packets)
	with receiver_patcher, sender_patcher:
		receiver = ReliableReceiver("127.0.0.1", 1)
		assert receiver.receive().payload == b"one"
		assert receiver.receive().payload == b"two"
		receiver.close()


def test_duplicate_out_of_order_data_is_not_buffered_twice():
	packets = [
		_authenticated_data(1, b"one"),
		_authenticated_data(3, b"three"),
		_authenticated_data(3, b"three"),
		_authenticated_data(2, b"two"),
	]
	receiver_patcher, sender_patcher, _, _ = _mock_receiver(packets)
	with receiver_patcher, sender_patcher:
		receiver = ReliableReceiver("127.0.0.1", 1)
		assert receiver.receive().payload == b"one"
		assert receiver.receive().payload == b"two"
		assert receiver._out_of_order == {}
		assert len(receiver._pending_delivery) == 1
		assert receiver.receive().payload == b"three"
		receiver.close()


def test_invalid_hmac_out_of_order_data_does_not_change_state():
	invalid_packet = _authenticated_data(3, b"forged")
	invalid_packet.authentication_tag = b"x" * 32
	receiver_patcher, sender_patcher, receiver_transport, _ = _mock_receiver(
		[invalid_packet]
	)
	with receiver_patcher, sender_patcher:
		receiver = ReliableReceiver("127.0.0.1", 1)
		receiver.receiver.receive.side_effect = [
			(invalid_packet, ("127.0.0.1", 1)),
			TimeoutError,
		]
		with pytest.raises(TimeoutError):
			receiver.receive()
		assert receiver.next_expected_sequence == 1
		assert receiver._out_of_order == {}
		assert receiver.duplicate_detector.is_duplicate(3) is False
		receiver.close()


def test_multiple_out_of_order_packets_are_delivered_in_order():
	packets = [
		_authenticated_data(1, b"one"),
		_authenticated_data(4, b"four"),
		_authenticated_data(3, b"three"),
		_authenticated_data(2, b"two"),
	]
	receiver_patcher, sender_patcher, _, _ = _mock_receiver(packets)
	with receiver_patcher, sender_patcher:
		receiver = ReliableReceiver("127.0.0.1", 1)
		assert receiver.receive().payload == b"one"
		assert receiver.receive().payload == b"two"
		assert receiver.receive().payload == b"three"
		assert receiver.receive().payload == b"four"
		receiver.close()


def test_out_of_order_buffer_has_a_fixed_limit():
	packets = [_authenticated_data(sequence, b"data") for sequence in range(2, 132)]
	receiver_patcher, sender_patcher, _, _ = _mock_receiver(packets)
	with receiver_patcher, sender_patcher:
		receiver = ReliableReceiver("127.0.0.1", 1)
		receiver.receiver.receive.side_effect = [
			(packet, ("127.0.0.1", 1)) for packet in packets
		] + [TimeoutError]
		with pytest.raises(TimeoutError):
			receiver.receive()
		assert len(receiver._out_of_order) == MAX_OUT_OF_ORDER_BUFFER_SIZE
		assert receiver.next_expected_sequence == 1
		receiver.close()
