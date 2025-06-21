
import struct
import socket
from ospf_daemon.config import ROUTER_ID
def ip_to_bytes(ip): return socket.inet_aton(ip)

def build_lsr_packet(requests):
    header = struct.pack("!BBH", 2, 3, 0)  # Version 2, Type 3 (LSR), Length placeholder
    header += ip_to_bytes(ROUTER_ID)  # Router ID (ejemplo)
    header += ip_to_bytes("0.0.0.0")      # Area ID
    header += b"\x00\x00"               # Checksum
    header += struct.pack("!H", 0)        # AuType
    header += struct.pack("!Q", 0)        # Authentication

    body = b""
    for req in requests:
        body += struct.pack("!I", req["type"])
        body += ip_to_bytes(req["lsa_id"])
        body += ip_to_bytes(req["adv_router"])

    pkt = header + body
    length = len(pkt)
    pkt = pkt[:2] + struct.pack("!H", length) + pkt[4:]
    return pkt
