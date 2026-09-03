import time

from ramp_udp.config.settings import authentication_enabled, get_secret_key
from ramp_udp.protocol.constants import DEFAULT_TIMEOUT, MAX_RETRANSMISSIONS
from ramp_udp.protocol.message_types import MessageType
from ramp_udp.protocol.packet import Packet
from ramp_udp.protocol.serializer import PacketSerializer
from ramp_udp.reliability.ack import AckManager
from ramp_udp.reliability.retransmission import RetransmissionManager
from ramp_udp.reliability.sequence import SequenceGenerator
from ramp_udp.reliability.timer import Timer
from ramp_udp.security.hmac_auth import generate_hmac, verify_hmac
from ramp_udp.transport.udp_sender import UDPSender
from ramp_udp.utils.metrics import ProtocolMetrics


class ReliableSender:
    def __init__(self, host: str, port: int):
        self.sender = UDPSender(host, port)
        self.secret_key = get_secret_key()
        self.authentication_enabled = authentication_enabled()
        self.metrics = ProtocolMetrics()
        self.sequence_generator = SequenceGenerator()
        self.timer = Timer(DEFAULT_TIMEOUT)

    def send(self, payload: bytes, destination: tuple[str, int]) -> bool:
        sequence_number = self.sequence_generator.next()
        packet = Packet(
            message_type=MessageType.DATA,
            sequence_number=sequence_number,
            payload=payload,
        )
        if self.authentication_enabled:
            packet.authentication_tag = generate_hmac(
                PacketSerializer.authentication_data(packet), self.secret_key
            )

        retransmissions = RetransmissionManager(MAX_RETRANSMISSIONS)
        started_at = time.monotonic()
        self.metrics.messages_sent += 1

        print(f"Sending DATA sequence={sequence_number}")
        self.sender.send(packet, destination)

        while True:
            print(f"Waiting for ACK sequence={sequence_number}")
            if self._wait_for_ack(sequence_number):
                print(f"ACK received sequence={sequence_number}")
                print("Transmission successful")
                self.metrics.successful_transmissions += 1
                self.metrics.record_latency(started_at)
                return True

            print("ACK timeout")

            if not retransmissions.can_retransmit():
                print(
                    f"Transmission failed after {retransmissions.count} "
                    f"retransmission(s)"
                )
                self.metrics.transmission_failures += 1
                return False

            attempt = retransmissions.record()
            print(
                f"Retransmitting DATA sequence={sequence_number} "
                f"(attempt {attempt})"
            )
            self.sender.send(packet, destination)
            self.metrics.retransmissions += 1

    def _wait_for_ack(self, sequence_number: int) -> bool:
        self.timer.start()

        while not self.timer.expired():
            remaining = self.timer.timeout - (time.monotonic() - self.timer.start_time)
            if remaining <= 0:
                break

            self.sender.set_timeout(remaining)

            try:
                data, _address = self.sender.receive()
            except TimeoutError:
                break

            try:
                response = PacketSerializer.deserialize(data)
            except (ValueError, OSError):
                continue

            if self.authentication_enabled and (
                not response.authentication_tag or not verify_hmac(
                PacketSerializer.authentication_data(response),
                response.authentication_tag,
                self.secret_key,
                )
            ):
                self.metrics.authentication_failures += 1
                print("Invalid ACK authentication")
                continue

            if AckManager.is_valid(response, sequence_number):
                return True

        return False

    def close(self) -> None:
        self.sender.close()
        self.metrics.write()
