import os

from ramp_udp.protocol.message_types import MessageType
from ramp_udp.protocol.packet import Packet
from ramp_udp.reliability.ack import AckManager
from ramp_udp.reliability.duplicate import DuplicateDetector
from ramp_udp.transport.udp_receiver import UDPReceiver
from ramp_udp.transport.udp_sender import UDPSender


class ReliableReceiver:
    def __init__(self, host: str, port: int):
        self.receiver = UDPReceiver(host, port)
        self.sender = UDPSender(host, port)
        self.duplicate_detector = DuplicateDetector()

        self._drop_first_ack = os.environ.get("DROP_FIRST_ACK") == "1"
        self._first_ack_dropped = False
        if self._drop_first_ack:
            print("Demo mode: DROP_FIRST_ACK=1 (first ACK will be dropped)")

    def receive(self) -> Packet:
        while True:
            packet, address = self.receiver.receive()

            if packet.message_type != MessageType.DATA:
                return packet

            is_duplicate = self.duplicate_detector.is_duplicate(
                packet.sequence_number
            )

            if is_duplicate:
                print(
                    f"Duplicate DATA sequence={packet.sequence_number} "
                    f"(ACK resent, not delivered)"
                )
            else:
                self.duplicate_detector.mark_delivered(packet.sequence_number)
                print(f"Delivering DATA sequence={packet.sequence_number}")

            ack = AckManager.create(packet.sequence_number)
            if self._should_drop_ack():
                print(
                    f"[demo] ACK dropped sequence={packet.sequence_number}"
                )
            else:
                self.sender.send(ack, address)
                if self._drop_first_ack:
                    print(
                        f"[demo] ACK sent sequence={packet.sequence_number}"
                    )

            if is_duplicate:
                continue

            return packet

    def _should_drop_ack(self) -> bool:
        if not self._drop_first_ack or self._first_ack_dropped:
            return False

        self._first_ack_dropped = True
        return True

    def close(self) -> None:
        self.receiver.close()
        self.sender.close()
