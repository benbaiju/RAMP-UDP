from ramp_udp.protocol.message_types import MessageType
from ramp_udp.protocol.packet import Packet
from ramp_udp.reliability.sequence import SequenceManager
from ramp_udp.reliability.timer import Timer
from ramp_udp.transport.sender import Sender
from ramp_udp.protocol.constants import DEFAULT_TIMEOUT


class ReliableSender:
    def __init__(self, host: str, port: int):
        self.sender = Sender(host, port)
        self.sequence_manager = SequenceManager()
        self.timer = Timer(DEFAULT_TIMEOUT)

    def send(self, payload: bytes, destination: tuple[str, int]) -> None:
        packet = Packet(
            message_type=MessageType.DATA,
            sequence_number=self.sequence_manager.next(),
            payload=payload,
        )

        self.sender.send(packet, destination)

    def close(self) -> None:
        self.sender.close()