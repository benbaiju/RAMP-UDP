from dataclasses import dataclass, field

from ramp_udp.protocol.constants import MAGIC_NUMBER, PROTOCOL_VERSION
from ramp_udp.protocol.message_types import MessageType


@dataclass(slots=True)
class Packet:
    message_type: MessageType
    sequence_number: int
    payload: bytes = field(default_factory=bytes)
    magic: bytes = MAGIC_NUMBER
    version: int = PROTOCOL_VERSION

    @property
    def payload_length(self) -> int:
        return len(self.payload)