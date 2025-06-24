import socket
import struct
import array
import socket
from db import neigborgs
from config import DESIGNATED_ROUTER


#RFC 1071
def ospf_fletcher_checksum(packet: bytes) -> int: 
    if len(packet) % 2 != 0:
        packet += b'\0'

    res = sum(array.array("H", packet))
    res = (res >> 16) + (res & 0xffff)
    res += res >> 16

    return (~res) & 0xffff

def ip_to_bytes(ip):
    return socket.inet_aton(ip)

def build_ospf_hello(router_id, area_id):
    version = 2
    type_ospf = 1  # Hello
    auth_type = 0  # No auth
    auth = b'\x00' * 8

    # Hello body: (Network mask + HelloInterval + ... etc.)
    # Esto es solo una plantilla mínima
    hello = (
        socket.inet_aton("255.255.255.0") +  # netmask
        struct.pack("!H", 10) +              # Hello interval
        b"\x02" +                            # Options
        b"\x01" +                            # Router priority
        struct.pack("!I", 40) +              # Dead interval
        socket.inet_aton(DESIGNATED_ROUTER) +        # Designated Router
        socket.inet_aton("0.0.0.0")         # Backup Designated Router
    )

    for neigbor in neigborgs:
        print(neigbor)
        hello+=socket.inet_aton(neigbor)

    pkt_len = 24 + len(hello)
    checksum = 0  # Placeholder (deberías calcularlo)

    header = struct.pack(
        "!BBH4s4sHBB8s",
        version, type_ospf, pkt_len,
        ip_to_bytes(router_id), ip_to_bytes(area_id),
        checksum, auth_type, 0,
        auth
    )

    pkt = header + hello
    length = len(pkt)
    pkt = pkt[:2] + struct.pack("!H", length) + pkt[4:]

    pkt_for_checksum = pkt[:12] + b"\x00\x00" + pkt[14:]
    chksum = ospf_fletcher_checksum(pkt_for_checksum)
    pkt = pkt[:12] + struct.pack("H", chksum) + pkt[14:]

    return pkt


