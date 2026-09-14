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

            if message == "/quit":
                print("Exiting chat.")
                break

            if not message:
                print("[sender] Empty message ignored.")
                continue

            try:
                success = sender.send(message.encode("utf-8"), CHAT_PEER)
            except Exception as error:
                print(f"[sender] Send error: {type(error).__name__}: {error}")
                continue

            if success:
                print("Message sent successfully.\n")
            else:
                print("Message failed to send.\n")
    except KeyboardInterrupt:
        print("\nExiting chat.")
    except EOFError:
        print("\n[sender] Input stream closed.")
    finally:
        sender.close()


if __name__ == "__main__":
    main()
