import socket
import fcntl
import struct

def get_mac_address(iface):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    info = fcntl.ioctl(
        s.fileno(),
        0x8927,  # SIOCGIFHWADDR
        struct.pack('256s', iface[:15].encode('utf-8'))
    )
    return ':'.join('%02x' % b for b in info[18:24])

