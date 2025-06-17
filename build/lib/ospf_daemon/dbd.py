
import socket, struct

def build_ospf_header(router_id, area_id, pkt_type, payload):
    version = 2
    length = 24 + len(payload)
    header = struct.pack("!BBH", version, pkt_type, length)
    header += socket.inet_aton(router_id)
    header += socket.inet_aton(area_id)
    header += b"\x00\x00"  # checksum
    header += struct.pack("!H", 0)  # AuType
    header += struct.pack("!Q", 0)  # Authentication
    return header + payload

def build_dbd_packet(router_id, mtu=1500, opts=0x02, flags=0x07, dd_seq=1):
    payload = struct.pack("!HBBI", mtu, opts, flags, dd_seq)
    return build_ospf_header(router_id, "0.0.0.0", 2, payload)
