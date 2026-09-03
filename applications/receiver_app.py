import os

from ramp_udp.transport.udp_receiver import UDPReceiver


def main():
    host = os.environ.get("RAMP_BIND_HOST", "127.0.0.1")
    port = int(os.environ.get("RAMP_PORT", "5001"))
    receiver = UDPReceiver(host, port)

    print("\n RAMP-UDP Receiver")
    print(f"\nListening on {host}:{port}...\n")

    packet, address = receiver.receive()

    print(f"Packet received from {address}")

    print("\nDeserializing packet...")
    print(" Packet deserialized")

    print(f"Magic           : {packet.magic.decode()}")
    print(f"Version         : {packet.version}")
    print(f"Message Type    : {packet.message_type.name}")
    print(f"Sequence Number : {packet.sequence_number}")
    print(f"Payload Length  : {packet.payload_length} bytes")
    print(f"Payload         : {packet.payload.decode()}")

    receiver.close()


if __name__ == "__main__":
    main()