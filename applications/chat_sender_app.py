import os

from ramp_udp.reliability.reliable_sender import ReliableSender

CHAT_HOST = os.environ.get("RAMP_LOCAL_HOST", "127.0.0.1")
CHAT_LOCAL_PORT = int(os.environ.get("RAMP_LOCAL_PORT", "6000"))
CHAT_PEER = (
    os.environ.get("RAMP_PEER_HOST", "127.0.0.1"),
    int(os.environ.get("RAMP_PEER_PORT", "6001")),
)


def main() -> None:
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
                continue

            success = sender.send(message.encode("utf-8"), CHAT_PEER)
            if success:
                print("Message sent successfully.\n")
            else:
                print("Message failed to send.\n")
    except KeyboardInterrupt:
        print("\nExiting chat.")
    finally:
        sender.close()


if __name__ == "__main__":
    main()
