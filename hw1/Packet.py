from __future__ import annotations


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
