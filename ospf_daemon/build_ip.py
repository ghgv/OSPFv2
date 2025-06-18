
import socket
import struct

def checksum(data):
    if len(data) % 2:
        data += b'\0'
    s = sum(struct.unpack("!%dH" % (len(data) // 2), data))
    s = (s >> 16) + (s & 0xffff)
    s += s >> 16
    return (~s) & 0xffff

def build_ip_header(src_ip, dst_ip, payload_len):
    version_ihl = 0x45
    tos = 0
    total_len = 20 + payload_len
    ident = 0
    flags_frag = 0x4000  # Don't Fragment
    ttl = 1
    proto = 89  # OSPF
    checksum_placeholder = 0

    src = socket.inet_aton(src_ip)
    dst = socket.inet_aton(dst_ip)

    header = struct.pack("!BBHHHBBH4s4s",
        version_ihl, tos, total_len, ident, flags_frag,
        ttl, proto, checksum_placeholder, src, dst
    )

    chksum = checksum(header)
    header = struct.pack("!BBHHHBBH4s4s",
        version_ihl, tos, total_len, ident, flags_frag,
        ttl, proto, chksum, src, dst
    )
    print("Header",header)
    return header
