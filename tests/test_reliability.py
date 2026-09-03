from unittest.mock import MagicMock, patch

from ramp_udp.config.settings import DEVELOPMENT_SECRET_KEY
from ramp_udp.protocol.constants import MAX_RETRANSMISSIONS
from ramp_udp.protocol.message_types import MessageType
from ramp_udp.protocol.packet import Packet
from ramp_udp.protocol.serializer import PacketSerializer
from ramp_udp.reliability.ack import AckManager
from ramp_udp.reliability.reliable_sender import ReliableSender
from ramp_udp.reliability.sequence import SequenceGenerator
from ramp_udp.security.hmac_auth import generate_hmac


class TestSequenceGenerator:
    def test_sequence_numbers_are_generated_correctly(self):
        generator = SequenceGenerator()

        assert generator.next() == 1
        assert generator.next() == 2
        assert generator.next() == 3

    def test_new_application_message_gets_next_sequence_number(self):
        generator = SequenceGenerator()

        first = generator.next()
        second = generator.next()

        assert second == first + 1

    def test_reset_restarts_sequence(self):
        generator = SequenceGenerator()
        generator.next()
        generator.next()
        generator.reset()

        assert generator.next() == 1


def _serialized_ack(sequence_number: int) -> bytes:
    ack = AckManager.create(sequence_number)
    ack.authentication_tag = generate_hmac(
        PacketSerializer.authentication_data(ack), DEVELOPMENT_SECRET_KEY
    )
    return PacketSerializer.serialize(ack)


class TestReliableSender:
    def test_successful_transmission_without_retransmission(self):
        mock_transport = MagicMock()
        mock_transport.receive.return_value = (
            _serialized_ack(1),
            ("127.0.0.1", 5001),
        )

        with patch(
            "ramp_udp.reliability.reliable_sender.UDPSender",
            return_value=mock_transport,
        ):
            sender = ReliableSender("127.0.0.1", 0)
            success = sender.send(b"hello", ("127.0.0.1", 5001))

        assert success is True
        assert mock_transport.send.call_count == 1

        sent_packet = mock_transport.send.call_args.args[0]
        assert sent_packet.message_type == MessageType.DATA
        assert sent_packet.sequence_number == 1
        assert sent_packet.payload == b"hello"

    def test_ack_timeout_causes_retransmission_of_same_data(self):
        mock_transport = MagicMock()
        mock_transport.receive.side_effect = [
            TimeoutError,
            (_serialized_ack(1), ("127.0.0.1", 5001)),
        ]

        with patch(
            "ramp_udp.reliability.reliable_sender.UDPSender",
            return_value=mock_transport,
        ):
            sender = ReliableSender("127.0.0.1", 0)
            success = sender.send(b"payload", ("127.0.0.1", 5001))

        assert success is True
        assert mock_transport.send.call_count == 2

        first_packet = mock_transport.send.call_args_list[0].args[0]
        second_packet = mock_transport.send.call_args_list[1].args[0]

        assert first_packet.sequence_number == second_packet.sequence_number == 1
        assert first_packet.payload == second_packet.payload == b"payload"
        assert first_packet.message_type == second_packet.message_type == MessageType.DATA

    def test_retransmission_does_not_generate_new_sequence_number(self):
        mock_transport = MagicMock()
        mock_transport.receive.side_effect = [
            TimeoutError,
            TimeoutError,
            (_serialized_ack(1), ("127.0.0.1", 5001)),
        ]

        with patch(
            "ramp_udp.reliability.reliable_sender.UDPSender",
            return_value=mock_transport,
        ):
            sender = ReliableSender("127.0.0.1", 0)
            success = sender.send(b"same-seq", ("127.0.0.1", 5001))

        assert success is True
        assert mock_transport.send.call_count == 3

        sequence_numbers = [
            call.args[0].sequence_number for call in mock_transport.send.call_args_list
        ]
        assert sequence_numbers == [1, 1, 1]

    def test_retransmitted_packet_retains_sequence_payload_and_type(self):
        mock_transport = MagicMock()
        mock_transport.receive.side_effect = [
            TimeoutError,
            (_serialized_ack(1), ("127.0.0.1", 5001)),
        ]

        with patch(
            "ramp_udp.reliability.reliable_sender.UDPSender",
            return_value=mock_transport,
        ):
            sender = ReliableSender("127.0.0.1", 0)
            sender.send(b"retain-me", ("127.0.0.1", 5001))

        original = mock_transport.send.call_args_list[0].args[0]
        retransmitted = mock_transport.send.call_args_list[1].args[0]

        assert retransmitted.sequence_number == original.sequence_number
        assert retransmitted.payload == original.payload
        assert retransmitted.message_type == original.message_type

    def test_ack_after_retransmission_stops_further_retransmissions(self):
        mock_transport = MagicMock()
        mock_transport.receive.side_effect = [
            TimeoutError,
            (_serialized_ack(1), ("127.0.0.1", 5001)),
        ]

        with patch(
            "ramp_udp.reliability.reliable_sender.UDPSender",
            return_value=mock_transport,
        ):
            sender = ReliableSender("127.0.0.1", 0)
            success = sender.send(b"after-retransmit", ("127.0.0.1", 5001))

        assert success is True
        assert mock_transport.send.call_count == 2

    def test_wrong_ack_sequence_is_not_accepted(self):
        mock_transport = MagicMock()
        mock_transport.receive.side_effect = [
            (_serialized_ack(99), ("127.0.0.1", 5001)),
            TimeoutError,
            (_serialized_ack(1), ("127.0.0.1", 5001)),
        ]

        with patch(
            "ramp_udp.reliability.reliable_sender.UDPSender",
            return_value=mock_transport,
        ):
            sender = ReliableSender("127.0.0.1", 0)
            success = sender.send(b"reject-wrong-ack", ("127.0.0.1", 5001))

        assert success is True
        # Initial send + one retransmission after wrong ACK then timeout.
        assert mock_transport.send.call_count == 2

    def test_non_ack_packet_is_not_accepted(self):
        non_ack = Packet(
            message_type=MessageType.DATA,
            sequence_number=1,
            payload=b"not-ack",
        )
        mock_transport = MagicMock()
        mock_transport.receive.side_effect = [
            (PacketSerializer.serialize(non_ack), ("127.0.0.1", 5001)),
            TimeoutError,
            (_serialized_ack(1), ("127.0.0.1", 5001)),
        ]

        with patch(
            "ramp_udp.reliability.reliable_sender.UDPSender",
            return_value=mock_transport,
        ):
            sender = ReliableSender("127.0.0.1", 0)
            success = sender.send(b"reject-non-ack", ("127.0.0.1", 5001))

        assert success is True
        assert mock_transport.send.call_count == 2

    def test_new_application_message_advances_sequence_number(self):
        mock_transport = MagicMock()
        mock_transport.receive.side_effect = [
            (_serialized_ack(1), ("127.0.0.1", 5001)),
            (_serialized_ack(2), ("127.0.0.1", 5001)),
        ]

        with patch(
            "ramp_udp.reliability.reliable_sender.UDPSender",
            return_value=mock_transport,
        ):
            sender = ReliableSender("127.0.0.1", 0)
            assert sender.send(b"first", ("127.0.0.1", 5001)) is True
            assert sender.send(b"second", ("127.0.0.1", 5001)) is True

        first_packet = mock_transport.send.call_args_list[0].args[0]
        second_packet = mock_transport.send.call_args_list[1].args[0]

        assert first_packet.sequence_number == 1
        assert second_packet.sequence_number == 2

    def test_maximum_retransmissions_reports_failure(self):
        mock_transport = MagicMock()
        mock_transport.receive.side_effect = TimeoutError

        with patch(
            "ramp_udp.reliability.reliable_sender.UDPSender",
            return_value=mock_transport,
        ):
            sender = ReliableSender("127.0.0.1", 0)
            success = sender.send(b"never-acked", ("127.0.0.1", 5001))

        assert success is False
        assert mock_transport.send.call_count == 1 + MAX_RETRANSMISSIONS

        sequence_numbers = {
            call.args[0].sequence_number for call in mock_transport.send.call_args_list
        }
        payloads = {call.args[0].payload for call in mock_transport.send.call_args_list}
        message_types = {
            call.args[0].message_type for call in mock_transport.send.call_args_list
        }

        assert sequence_numbers == {1}
        assert payloads == {b"never-acked"}
        assert message_types == {MessageType.DATA}
