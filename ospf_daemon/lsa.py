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
        print(f"[🔍] Intentando parsear LSA de {len(data)} bytes")

        if len(data) < 20:
            raise ValueError(f"LSA demasiado corto: se esperaban al menos 20 bytes, se recibieron {len(data)}")

        try:
            num_lsa = struct.unpack("!HH", data[:4])
            data = data[4:]
            age, options, lsa_type = struct.unpack("!HBB", data[:4])
            lsa_id = socket.inet_ntoa(data[4:8])
            adv_router = socket.inet_ntoa(data[8:12])
            seq = struct.unpack("!I", data[12:16])[0]
            checksum, length = struct.unpack("!HH", data[16:20])
            print(checksum)
            print(length)
            #length, checksum  = struct.unpack("!HH", data[16:20])

            if len(data) < length:
                raise ValueError(f"LSA incompleto: se esperaban {length} bytes, se recibieron {len(data)}")

            # Enlace de datos (simplificado: cada uno 12 bytes)
            links = []
            offset = 20
            while offset + 12 <= len(data):
                to = socket.inet_ntoa(data[offset:offset+4])
                mask = socket.inet_ntoa(data[offset+4:offset+8])
                metric = struct.unpack("!I", data[offset+8:offset+12])[0]
                links.append((to, mask, metric))
                offset += 12

            return {
                "type": lsa_type,
                "lsa_id": lsa_id,
                "adv_router": adv_router,
                "seq": seq,
                "checksum": checksum,
                "length": length,
                "links": links
            }

        except struct.error as e:
            raise ValueError(f"Error desempaquetando LSA: {e}")