from ramp_udp.protocol.message_types import MessageType
from ramp_udp.protocol.packet import Packet
from ramp_udp.reliability.ack import AckManager


class TestAckCreation:
    def test_data_packet_produces_expected_ack(self):
        data = Packet(
            message_type=MessageType.DATA,
            sequence_number=7,
            payload=b"hello",
        )

        ack = AckManager.create(data.sequence_number)

        assert ack.message_type == MessageType.ACK
        assert ack.sequence_number == data.sequence_number
        assert ack.payload == b""

    def test_ack_has_message_type_ack(self):
        ack = AckManager.create(1)

        assert ack.message_type == MessageType.ACK
        assert AckManager.is_ack(ack) is True

    def test_ack_contains_correct_sequence_number(self):
        ack = AckManager.create(42)

        assert ack.sequence_number == 42


class TestAckValidation:
    def test_matching_ack_is_valid(self):
        ack = AckManager.create(3)

        assert AckManager.is_valid(ack, 3) is True

    def test_wrong_sequence_number_is_rejected(self):
        ack = AckManager.create(3)

        assert AckManager.is_valid(ack, 4) is False
        assert AckManager.is_valid(ack, 0) is False

    def test_data_packet_is_not_accepted_as_ack(self):
        data = Packet(
            message_type=MessageType.DATA,
            sequence_number=3,
            payload=b"not-an-ack",
        )

        assert AckManager.is_ack(data) is False
        assert AckManager.is_valid(data, 3) is False

    def test_non_ack_packet_is_not_accepted_as_ack(self):
        # Same sequence number, but wrong message type.
        packet = Packet(
            message_type=MessageType.DATA,
            sequence_number=9,
            payload=b"",
        )

        assert AckManager.is_valid(packet, 9) is False
