from ramp_udp.transport.receiver import Receiver


def main():
    receiver = Receiver("127.0.0.1", 5001)

    packet, address = receiver.receive()

    print(f"Received from {address}")
    print(packet)

    receiver.close()


if __name__ == "__main__":
    main()