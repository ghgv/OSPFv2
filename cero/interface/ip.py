import socket
import struct

def ip_to_bytes(ip):
    return socket.inet_aton(ip)

def checksum(data):
    if len(data) % 2 != 0:
        data += b'\x00'
    s = sum(struct.unpack("!%dH" % (len(data)//2), data))
    while s > 0xffff:
        s = (s & 0xffff) + (s >> 16)
    return ~s & 0xffff

def build_ip_packet(src_ip=None, dst_ip=None, proto=None, payload=None):
    version = 4
    ihl = 5  # Header length in 32-bit words
    ver_ihl = (version << 4) + ihl
    tos = 0
    total_length = 20 + len(payload)
    identification = 54321
    flags_offset = 0
    ttl = 1
    protocol = proto
    header_checksum = 0
    src_ip_bytes = ip_to_bytes(src_ip)
    dst_ip_bytes = ip_to_bytes(dst_ip)

    ip_header = struct.pack("!BBHHHBBH4s4s",
                            ver_ihl, tos, total_length,
                            identification, flags_offset,
                            ttl, protocol, header_checksum,
                            src_ip_bytes, dst_ip_bytes)

    header_checksum = checksum(ip_header)

    ip_header = struct.pack("!BBHHHBBH4s4s",
                            ver_ihl, tos, total_length,
                            identification, flags_offset,
                            ttl, protocol, header_checksum,
                            src_ip_bytes, dst_ip_bytes)

    return ip_header + payload
