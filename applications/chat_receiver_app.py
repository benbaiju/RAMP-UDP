import os

from ramp_udp.reliability.reliable_receiver import ReliableReceiver

CHAT_HOST = os.environ.get("RAMP_BIND_HOST", "127.0.0.1")
CHAT_PORT = int(os.environ.get("RAMP_PORT", "6001"))


def main() -> None:
    print("[receiver] Configuration:")
    print(f"[receiver] Listening address: {CHAT_HOST}:{CHAT_PORT}")
    print(
        f"[receiver] Authentication: "
        f"{os.environ.get('RAMP_AUTH_ENABLED', '1') != '0'}"
    )
    print("[receiver] Decryption: not applicable; payload is plaintext")
    receiver = ReliableReceiver(CHAT_HOST, CHAT_PORT)

    print("\n RAMP-UDP Chat")
    print("Waiting for messages...\n")

    try:
        while True:
            packet = receiver.receive()
            message = packet.payload.decode("utf-8")
            print(f"Peer: {message}")
    except KeyboardInterrupt:
        print("\nExiting chat.")
    except UnicodeDecodeError as error:
        print(f"\n[receiver] UTF-8 decode error: {error}")
    except OSError as error:
        print(f"\n[receiver] Socket error: {error}")
    finally:
        receiver.close()


if __name__ == "__main__":
    main()
