from ramp_udp.protocol.constants import MAX_RETRANSMISSIONS


class RetransmissionManager:
    def __init__(self, max_retransmissions: int = MAX_RETRANSMISSIONS):
        self.max_retransmissions = max_retransmissions
        self._count = 0

    @property
    def count(self) -> int:
        return self._count

    def can_retransmit(self) -> bool:
        return self._count < self.max_retransmissions

    def record(self) -> int:
        self._count += 1
        return self._count
