class SequenceGenerator:
    def __init__(self):
        self._current = 0

    def next(self) -> int:
        self._current += 1
        return self._current

    def reset(self) -> None:
        self._current = 0