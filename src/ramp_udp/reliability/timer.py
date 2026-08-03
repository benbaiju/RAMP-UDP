import time


class Timer:
    def __init__(self, timeout: float):
        self.timeout = timeout
        self.start_time = 0.0

    def start(self) -> None:
        self.start_time = time.monotonic()

    def expired(self) -> bool:
        return (time.monotonic() - self.start_time) >= self.timeout

    def reset(self) -> None:
        self.start()