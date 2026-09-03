import os
from collections import deque

from ramp_udp.config.settings import authentication_enabled, get_secret_key
from ramp_udp.protocol.constants import MAX_OUT_OF_ORDER_BUFFER_SIZE
from ramp_udp.protocol.message_types import MessageType
from ramp_udp.protocol.packet import Packet
from ramp_udp.protocol.serializer import PacketSerializer
from ramp_udp.reliability.ack import AckManager
from ramp_udp.reliability.duplicate import DuplicateDetector
from ramp_udp.security.hmac_auth import generate_hmac, verify_hmac
from ramp_udp.transport.udp_receiver import UDPReceiver
from ramp_udp.transport.udp_sender import UDPSender
from ramp_udp.utils.metrics import ProtocolMetrics


class ReliableReceiver:
    def __init__(self, host: str, port: int):
        self.receiver = UDPReceiver(host, port)
        self.sender = UDPSender(host, port)
        self.secret_key = get_secret_key()
        self.authentication_enabled = authentication_enabled()
        self.metrics = ProtocolMetrics()
        self.duplicate_detector = DuplicateDetector()
        self.next_expected_sequence = 1
        self._out_of_order: dict[int, tuple[Packet, tuple[str, int]]] = {}
        self._pending_delivery: deque[Packet] = deque()

        self._drop_first_ack = os.environ.get("DROP_FIRST_ACK") == "1"
        self._first_ack_dropped = False
        if self._drop_first_ack:
            print("Demo mode: DROP_FIRST_ACK=1 (first ACK will be dropped)")

    def receive(self) -> Packet:
        while True:
            if self._pending_delivery:
                return self._pending_delivery.popleft()

            packet, address = self.receiver.receive()

            if self.authentication_enabled and (
                not packet.authentication_tag or not verify_hmac(
                PacketSerializer.authentication_data(packet),
                packet.authentication_tag,
                self.secret_key,
                )
            ):
                self.metrics.authentication_failures += 1
                print("Invalid DATA authentication")
                continue

            if packet.message_type != MessageType.DATA:
                return packet

            sequence_number = packet.sequence_number
            if self.duplicate_detector.is_duplicate(sequence_number):
                print(
                    f"Duplicate DATA sequence={sequence_number} "
                    f"(ACK resent, not delivered)"
                )
                self.metrics.duplicates += 1
                self._send_ack(packet, address)
                continue

            if sequence_number in self._out_of_order:
                print(
                    f"Duplicate out-of-order DATA sequence={sequence_number} "
                    f"(already buffered)"
                )
                self.metrics.duplicates += 1
                continue

            if sequence_number < self.next_expected_sequence:
                print(
                    f"Stale DATA sequence={sequence_number} "
                    f"(expected {self.next_expected_sequence})"
                )
                self.metrics.duplicates += 1
                self._send_ack(packet, address)
                continue

            if sequence_number > self.next_expected_sequence:
                self.metrics.out_of_order_packets += 1
                if len(self._out_of_order) >= MAX_OUT_OF_ORDER_BUFFER_SIZE:
                    print("Out-of-order buffer full; DATA discarded")
                    continue
                self._out_of_order[sequence_number] = (packet, address)
                print(
                    f"Out-of-order DATA sequence={sequence_number} "
                    f"(expected {self.next_expected_sequence}, buffered)"
                )
                continue

            self._accept_in_order(packet, address)
            return self._pending_delivery.popleft()

    def _accept_in_order(
        self, packet: Packet, address: tuple[str, int]
    ) -> None:
        self.duplicate_detector.mark_delivered(packet.sequence_number)
        self.metrics.messages_delivered += 1
        self.next_expected_sequence += 1
        self._pending_delivery.append(packet)
        print(f"Delivering DATA sequence={packet.sequence_number}")
        self._send_ack(packet, address)

        while self.next_expected_sequence in self._out_of_order:
            buffered_packet, buffered_address = self._out_of_order.pop(
                self.next_expected_sequence
            )
            self._accept_in_order(buffered_packet, buffered_address)

    def _send_ack(self, packet: Packet, address: tuple[str, int]) -> None:
        ack = AckManager.create(packet.sequence_number)
        if self._should_drop_ack():
            print(f"[demo] ACK dropped sequence={packet.sequence_number}")
            return

        if self.authentication_enabled:
            ack.authentication_tag = generate_hmac(
                PacketSerializer.authentication_data(ack), self.secret_key
            )
        self.sender.send(ack, address)
        if self._drop_first_ack:
            print(f"[demo] ACK sent sequence={packet.sequence_number}")

    def _should_drop_ack(self) -> bool:
        if not self._drop_first_ack or self._first_ack_dropped:
            return False

        self._first_ack_dropped = True
        return True

    def close(self) -> None:
        self.receiver.close()
        self.sender.close()
        self.metrics.write()
