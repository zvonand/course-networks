from __future__ import annotations
import socket


HEADER_SIZE = 8
MAX_PAYLOAD_SIZE = 2**15 - HEADER_SIZE # using 2**16 (max UDP datagram size) gives OSError

class UDPBasedProtocol:
    def __init__(self, *, local_addr, remote_addr):
        self.udp_socket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
        self.remote_addr = remote_addr
        self.udp_socket.bind(local_addr)
        self.udp_socket.settimeout(0.00001)

    def sendto(self, data):
        return self.udp_socket.sendto(data, self.remote_addr)

    def recvfrom(self, n):
        msg, addr = self.udp_socket.recvfrom(n)
        return msg


class Packet():
    def __init__(self, seq_num_ : int, ack_num_ : int, data_ : bytes = b""):
        self.seq_num = seq_num_
        self.ack_num = ack_num_
        self.data = data_

    def serialize(self) -> bytes:
        seq = self.seq_num.to_bytes(4, byteorder="big")
        ack = self.ack_num.to_bytes(4, byteorder="big")
        return seq + ack + self.data

    @staticmethod
    def deserialize(data : bytes) -> Packet:
        seq = int.from_bytes(data[0:4], byteorder="big")
        ack = int.from_bytes(data[4:8], byteorder="big")
        return Packet(seq, ack, data[8:])
