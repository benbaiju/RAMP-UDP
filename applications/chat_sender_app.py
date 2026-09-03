import os

from ramp_udp.reliability.reliable_sender import ReliableSender

CHAT_HOST = os.environ.get("RAMP_LOCAL_HOST", "127.0.0.1")
CHAT_LOCAL_PORT = int(os.environ.get("RAMP_LOCAL_PORT", "6000"))
CHAT_PEER = (
    os.environ.get("RAMP_PEER_HOST", "127.0.0.1"),
    int(os.environ.get("RAMP_PEER_PORT", "6001")),
)


def main() -> None:
    print("[sender] Configuration:")
    print(f"[sender] Local address: {CHAT_HOST}:{CHAT_LOCAL_PORT}")
    print(f"[sender] Peer address : {CHAT_PEER[0]}:{CHAT_PEER[1]}")
    print(
        f"[sender] Authentication: "
        f"{os.environ.get('RAMP_AUTH_ENABLED', '1') != '0'}"
    )
    print("[sender] Encryption: not implemented; payload remains plaintext")
    sender = ReliableSender(CHAT_HOST, CHAT_LOCAL_PORT)

    print("\n RAMP-UDP Chat")
    print("Type a message or /quit\n")

    try:
        while True:
            message = input("You: ").strip()
            message_bytes = message.encode("utf-8")
            print(
                f"[sender] Input received: characters={len(message)}, "
                f"bytes={len(message_bytes)}"
            )
            print(f"[sender] Message content: {message!r}")

            if message == "/quit":
                print("[sender] Quit command received.")
                print("Exiting chat.")
                break

            if not message:
                print("[sender] Empty message ignored.")
                continue

            print(
                f"[sender] Sending {len(message_bytes)} bytes to "
                f"{CHAT_PEER[0]}:{CHAT_PEER[1]}..."
            )
            try:
                success = sender.send(message_bytes, CHAT_PEER)
            except Exception as error:
                print(f"[sender] Send error: {type(error).__name__}: {error}")
                continue

            print(f"[sender] Send result: success={success}")
            if success:
                print("Message sent successfully.\n")
            else:
                print("Message failed to send.\n")
    except KeyboardInterrupt:
        print("\nExiting chat.")
    except EOFError:
        print("\n[sender] Input stream closed.")
    finally:
        print("[sender] Closing sender.")
        sender.close()


if __name__ == "__main__":
    main()
