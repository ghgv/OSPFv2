import struct
import socket

LSA_TYPE_ROUTER = 1
OSPF_LSA_HEADER_LEN = 20

def ip_to_bytes(ip):
    return socket.inet_aton(ip)

def bytes_to_ip(b):
    return socket.inet_ntoa(b)

def ospf_fletcher_checksum(data):
    c0 = 0
    c1 = 0
    for b in data:
        c0 = (c0 + b) % 255
        c1 = (c1 + c0) % 255
    x = ((len(data) - 1) * c0 - c1) % 255
    if x <= 0: x += 255
    y = 510 - c0 - x
    if y > 255: y -= 255
    return bytes([x, y])

class RouterLSA:
    def __init__(self, adv_router, links, seq_num=None):
        self.age = 1
        self.type = LSA_TYPE_ROUTER
        self.id = adv_router
        self.adv_router = adv_router
        self.seq_num = seq_num if seq_num else 0x80000001
        self.links = links
        self.checksum = b'\x00\x00'

    def build(self):
        lsa_body = struct.pack("!B3xH", 0x01, len(self.links))
        for link_id, link_data, link_type, metric in self.links:
            lsa_body += ip_to_bytes(link_id)
            lsa_body += ip_to_bytes(link_data)
            lsa_body += struct.pack("!BBH", link_type, 0, metric)
        lsa_len = OSPF_LSA_HEADER_LEN + len(lsa_body)
        lsa_header = struct.pack("!HBB4s4sI2sH",
            self.age, self.type, 0,
            ip_to_bytes(self.id),
            ip_to_bytes(self.adv_router),
            self.seq_num,
            b'\x00\x00',
            lsa_len
        )
        chk_data = lsa_header[2:] + lsa_body
        self.checksum = ospf_fletcher_checksum(chk_data)
        lsa_header = struct.pack("!HBB4s4sI2sH",
            self.age, self.type, 0,
            ip_to_bytes(self.id),
            ip_to_bytes(self.adv_router),
            self.seq_num,
            self.checksum,
            lsa_len
        )
        return lsa_header + lsa_body

    @staticmethod
    def parse(data):
        age, lsa_type, _, lsa_id, adv_router, seq_num, checksum, length = struct.unpack("!HBB4s4sI2sH", data[:20])
        flags_links = struct.unpack("!B3xH", data[20:24])
        flags = flags_links[0]
        num_links = flags_links[1]
        links = []
        offset = 24
        for _ in range(num_links):
            link_id = bytes_to_ip(data[offset:offset+4])
            link_data = bytes_to_ip(data[offset+4:offset+8])
            link_type, _, metric = struct.unpack("!BBH", data[offset+8:offset+12])
            links.append((link_id, link_data, link_type, metric))
            offset += 12
        return {
            'lsa_id': bytes_to_ip(lsa_id),
            'adv_router': bytes_to_ip(adv_router),
            'seq': seq_num,
            'checksum': checksum,
            'links': links
        }