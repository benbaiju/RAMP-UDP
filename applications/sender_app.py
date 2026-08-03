from ramp_udp.protocol.message_types import MessageType
from ramp_udp.protocol.packet import Packet
from ramp_udp.transport.sender import Sender


def main():
    sender = Sender("127.0.0.1", 5000)

    packet = Packet(
        message_type=MessageType.DATA,
        sequence_number=1,
        payload=b"Hello RAMP-UDP",
    )

    sender.send(packet, ("127.0.0.1", 5001))
    sender.close()


if __name__ == "__main__":
    main()