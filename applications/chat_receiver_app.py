from ramp_udp.reliability.reliable_receiver import ReliableReceiver

CHAT_HOST = "127.0.0.1"
CHAT_PORT = 6001


def main() -> None:
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
    finally:
        receiver.close()


if __name__ == "__main__":
    main()
