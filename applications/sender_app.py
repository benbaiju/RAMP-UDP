import os

from ramp_udp.protocol.message_types import MessageType
from ramp_udp.protocol.packet import Packet
from ramp_udp.protocol.serializer import PacketSerializer
from ramp_udp.transport.udp_sender import UDPSender


def main():
    sender = UDPSender(
        os.environ.get("RAMP_LOCAL_HOST", "127.0.0.1"),
        int(os.environ.get("RAMP_LOCAL_PORT", "5000")),
    )
    destination = (
        os.environ.get("RAMP_PEER_HOST", "127.0.0.1"),
        int(os.environ.get("RAMP_PEER_PORT", "5001")),
    )

    packet = Packet(
        message_type=MessageType.DATA,
        sequence_number=33,
        payload=b"TEST",
    )

    print("\n RAMP-UDP Sender Application")

    print("\nCreating packet...")
    print(" Packet created")

    print(f"Message Type    : {packet.message_type.name}")
    print(f"Sequence Number : {packet.sequence_number}")
    print(f"Payload Length  : {packet.payload_length} bytes")
    print(f"Payload         : {packet.payload.decode()}")

    print("\nSerializing packet...")
    data = PacketSerializer.serialize(packet)
    print(" Packet serialized")
    print(f"Packet Size     : {len(data)} bytes")

    print("\nSending packet...")
    sender.send(packet, destination)
    print(" Packet sent")

    sender.close()


if __name__ == "__main__":
    main()