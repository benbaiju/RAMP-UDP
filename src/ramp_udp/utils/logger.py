import os


def debug(message: str) -> None:
    if os.environ.get("RAMP_VERBOSE", "0") != "0":
        print(message)
