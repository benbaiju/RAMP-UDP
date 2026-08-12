import time

from ramp_udp.protocol.constants import DEFAULT_TIMEOUT, MAX_RETRANSMISSIONS
from ramp_udp.protocol.message_types import MessageType
from ramp_udp.protocol.packet import Packet
from ramp_udp.protocol.serializer import PacketSerializer
from ramp_udp.reliability.ack import AckManager
from ramp_udp.reliability.retransmission import RetransmissionManager
from ramp_udp.reliability.sequence import SequenceGenerator
from ramp_udp.reliability.timer import Timer
from ramp_udp.transport.udp_sender import UDPSender


class ReliableSender:
    def __init__(self, host: str, port: int):
        self.sender = UDPSender(host, port)
        self.sequence_generator = SequenceGenerator()
        self.timer = Timer(DEFAULT_TIMEOUT)

    def send(self, payload: bytes, destination: tuple[str, int]) -> bool:
        sequence_number = self.sequence_generator.next()
        packet = Packet(
            message_type=MessageType.DATA,
            sequence_number=sequence_number,
            payload=payload,
        )

        retransmissions = RetransmissionManager(MAX_RETRANSMISSIONS)

        print(f"Sending DATA sequence={sequence_number}")
        self.sender.send(packet, destination)

        while True:
            print(f"Waiting for ACK sequence={sequence_number}")
            if self._wait_for_ack(sequence_number):
                print(f"ACK received sequence={sequence_number}")
                print("Transmission successful")
                return True

            print("ACK timeout")

            if not retransmissions.can_retransmit():
                print(
                    f"Transmission failed after {retransmissions.count} "
                    f"retransmission(s)"
                )
                return False

            attempt = retransmissions.record()
            print(
                f"Retransmitting DATA sequence={sequence_number} "
                f"(attempt {attempt})"
            )
            self.sender.send(packet, destination)

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

            if AckManager.is_valid(response, sequence_number):
                return True

        return False

    def close(self) -> None:
        self.sender.close()
