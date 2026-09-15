#!/usr/bin/env python3

import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC = REPO_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from ramp_udp.config.settings import get_secret_key
from ramp_udp.protocol.message_types import MessageType
from ramp_udp.protocol.packet import Packet
from ramp_udp.protocol.serializer import PacketSerializer
from ramp_udp.security.hmac_auth import generate_hmac
from ramp_udp.transport.udp_sender import UDPSender

ORIGINAL_PAYLOAD = b"authentic-message"
LOCAL_HOST = os.environ.get("RAMP_LOCAL_HOST", "10.0.0.1")
LOCAL_PORT = int(os.environ.get("RAMP_LOCAL_PORT", "6000"))
PEER = (
    os.environ.get("RAMP_PEER_HOST", "10.0.0.2"),
    int(os.environ.get("RAMP_PEER_PORT", "6001")),
)


def _tamper_one_byte(payload: bytes) -> bytes:
    if not payload:
        raise ValueError("Payload must not be empty.")
    return bytes([payload[0] ^ 0x01]) + payload[1:]


def main() -> int:
    secret_key = get_secret_key()

    packet = Packet(
        message_type=MessageType.DATA,
        sequence_number=1,
        payload=ORIGINAL_PAYLOAD,
    )
    packet.authentication_tag = generate_hmac(
        PacketSerializer.authentication_data(packet),
        secret_key,
    )
    hmac_before_tamper = packet.authentication_tag

    packet.payload = _tamper_one_byte(ORIGINAL_PAYLOAD)

    print("RAMP-UDP HMAC tampering demonstration")
    print(f"From {LOCAL_HOST}:{LOCAL_PORT} -> {PEER[0]}:{PEER[1]}")
    print(f"Original payload : {ORIGINAL_PAYLOAD!r}")
    print(f"Tampered payload : {packet.payload!r}  (one byte flipped after HMAC)")
    print(f"HMAC calculated  : before payload modification")
    print(f"HMAC sent        : {hmac_before_tamper.hex()}  (unchanged original tag)")
    print("Receiver should print: Invalid DATA authentication")
    print("Receiver should NOT deliver the tampered payload.")

    sender = UDPSender(LOCAL_HOST, LOCAL_PORT)
    try:
        sender.send(packet, PEER)
        print("Tampered DATA packet sent.")
    finally:
        sender.close()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
