from socket import timeout as SocketTimeoutError

from common import UDPBasedProtocol, Packet, MAX_PAYLOAD_SIZE, HEADER_SIZE


class MyTCPProtocol(UDPBasedProtocol):
    def __init__(self, *args, **kwargs):
        self.seq_num = 0
        self.ack_num = 1
        self._ingress = []
        self._egress_window = []
        self._read_buffer = b""

        super().__init__(*args, **kwargs)

    def _wait_acks(self):
        packets = self._recv()
        for packet in packets:
            while len(self._egress_window) != 0:
                first_egress_packet = self._egress_window[0]
                if packet.ack_num > first_egress_packet.seq_num + len(first_egress_packet.data):
                    self._egress_window.pop(0)
                else:
                    break

    def _recv(self):
        buf = self.recvfrom(100 * MAX_PAYLOAD_SIZE)
        offset = 0
        packets = []
        while offset < len(buf):
            packet = Packet.deserialize(buf[offset:])
            offset += HEADER_SIZE + len(packet.data)
            packets.append(packet)

        return packets

    def _reorder(self) -> bytes:
        data = b""
        self._ingress.sort(key = lambda packet : packet.seq_num)
        while len(self._ingress) != 0:
            first_incoming = self._ingress[0]

            if self.ack_num >= first_incoming.seq_num + 1:
                self._ingress.pop(0)

                if self.ack_num == first_incoming.seq_num + 1:
                    self.ack_num = first_incoming.seq_num + len(first_incoming.data) + 1
                    data += first_incoming.data
            else:
                break

        return data
    
    def _send(self, packet : Packet, ordinary = True) -> int:
        if ordinary:
            self.seq_num += len(packet.data)

        return self.sendto(packet.serialize()) - HEADER_SIZE
    
    def _ack(self):
        packet = Packet(self.seq_num, self.ack_num)
        self._send(packet)
    
    # As it is a "reliable" protocol, it must be sync
    def send(self, data: bytes) -> int:
        bytes_sent = 0
        data_len = len(data)

        while bytes_sent < data_len:
            payload = data[bytes_sent:min(bytes_sent + MAX_PAYLOAD_SIZE, data_len)]
            packet = Packet(self.seq_num, self.ack_num, payload)
            self._send(packet)
            self._egress_window.append(packet)
            bytes_sent += len(payload)

        while len(self._egress_window):
            try:
                self._wait_acks()
            except SocketTimeoutError:
                for packet in self._egress_window:
                    self._send(packet, False)

        return bytes_sent

    def recv(self, n: int) -> bytes:
        data = b""
        
        if len(self._read_buffer):
            read_from_buffer = min(n, len(self._read_buffer))
            data += self._read_buffer[:read_from_buffer]
            self._read_buffer = self._read_buffer[read_from_buffer:]
        
        while len(data) < n:
            try:
                packets = self._recv()
                self._ingress.extend(packets)
                data += self._reorder()                    
            except SocketTimeoutError:
                self._ack()

        self._ack()
        
        if len(data) > n:
            self._read_buffer += data[n:]
        
        return data[:n]
