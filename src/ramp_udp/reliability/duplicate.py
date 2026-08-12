class DuplicateDetector:
    def __init__(self):
        self._delivered: set[int] = set()

    def is_duplicate(self, sequence_number: int) -> bool:
        return sequence_number in self._delivered

    def mark_delivered(self, sequence_number: int) -> None:
        self._delivered.add(sequence_number)
