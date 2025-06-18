
import socket
import struct
import time
import array

from ospf_daemon.config import ROUTER_ID, HELLO_INTERVAL, INTERFACES
from ospf_daemon.neighbors import neighbors
from ospf_daemon.dbd import build_dbd_packet
from ospf_daemon.build_ip import build_ip_header

IP_SALIDA = "192.168.3.3"

def ip_to_bytes(ip):
    return socket.inet_aton(ip)

def ip_from_bytes(b: bytes) -> str:
    return socket.inet_ntoa(b)

#def ospf_fletcher_checksum(data): OSPF en RFC 2328 
def ospf_fletcher_checksum1(data: bytes) -> int:
    c0 = 0
    c1 = 0
    for b in data:
        c0 = (c0 + b) % 255
        c1 = (c1 + c0) % 255
    x = ((len(data) - 1) * c0 - c1) % 255
    if x <= 0:
        x += 255
    y = 510 - c0 - x
    if y > 255:
        y -= 255
    return (x << 8) + y  # 👈 RETORNA UN ENTERO

#RFC 1071
def ospf_fletcher_checksum(packet: bytes) -> int: 
    if len(packet) % 2 != 0:
        packet += b'\0'

    res = sum(array.array("H", packet))
    res = (res >> 16) + (res & 0xffff)
    res += res >> 16

    return (~res) & 0xffff

def build_hello_packet(router_id, neighbors=[]):
    version = 2
    type_ = 1

    netmask = ip_to_bytes("255.255.255.0")
    hello_interval = HELLO_INTERVAL
    options = 2
    priority = 1
    dead_interval = hello_interval * 4
    dr = ip_to_bytes(router_id)
    bdr = ip_to_bytes("0.0.0.0")

    body = netmask
    body += struct.pack("!HBBI", hello_interval, options, priority, dead_interval)
    body += dr + bdr
    for n in neighbors:
        body += ip_to_bytes(n)

    header = struct.pack("!BBH", version, type_, 0)
    header += ip_to_bytes(router_id)
    header += ip_to_bytes("0.0.0.0")
    header += b"\x00\x00"
    header += struct.pack("!H", 0)
    header += struct.pack("!Q", 0)

    pkt = header + body
    length = len(pkt)
    pkt = pkt[:2] + struct.pack("!H", length) + pkt[4:]

    pkt_for_checksum = pkt[:12] + b"\x00\x00" + pkt[14:]
    chksum = ospf_fletcher_checksum(pkt_for_checksum)
    pkt = pkt[:12] + struct.pack("H", chksum) + pkt[14:]
    return pkt    

#RFC 2328, sección A.3.2?
def build_hello_packet1(router_id, neighbors=[]):
    version = 2
    type_ = 1

    # Hello body (20 bytes + vecinos)
    netmask = ip_to_bytes("255.255.255.0")
    hello_interval = HELLO_INTERVAL
    options = 2
    priority = 1
    dead_interval = hello_interval * 4
    dr = ip_to_bytes(router_id)
    bdr = ip_to_bytes("0.0.0.0")

    body = netmask
    body += struct.pack("!HBBI", hello_interval, options, priority, dead_interval)
    body += dr + bdr
    for n in neighbors:
        body += ip_to_bytes(n)

    # Cabecera OSPF (24 bytes)
    header = struct.pack("!BBH", version, type_, 0)               # version, type, length placeholder
    header += ip_to_bytes(router_id)                              # Router ID
    header += ip_to_bytes("0.0.0.0")                              # Area ID
    header += b"\x00\x00"                                         # Checksum placeholder
    header += struct.pack("!H", 0)                                # AuType
    header += struct.pack("!Q", 0)                                # Auth (8 bytes)

    pkt = header + body
    length = len(pkt)
    pkt = pkt[:2] + struct.pack("!H", length) + pkt[4:]           # insert real length

    # Insertar checksum en offset 12–13 después de haber seteado a cero
    pkt_for_checksum = pkt[:12] + b"\x00\x00" + pkt[14:]        # cero temporal
    chksum = ospf_fletcher_checksum(pkt_for_checksum)
    print(struct.pack("H", chksum).hex())
    pkt = pkt[:12] + struct.pack("H", chksum) + pkt[14:]
    return pkt

def send_hello_periodically():
    
    sock = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_RAW)
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_IF, socket.inet_aton(IP_SALIDA))
    while True:
        hello_pkt = build_hello_packet(ROUTER_ID,neighbors)
        ip_hdr = build_ip_header(IP_SALIDA, "224.0.0.5", len(hello_pkt))
        full_pkt = ip_hdr + hello_pkt
        sock.sendto(full_pkt, ("224.0.0.5", 0))
        print(f"[📣] Hello enviado desde {ROUTER_ID} por IP {IP_SALIDA}")
        time.sleep(HELLO_INTERVAL)

def parse_hello_packet(pkt):
    if len(pkt) < 44: return None
    router_id = ip_from_bytes(pkt[4:8])
    netmask = ip_from_bytes(pkt[24:28])
    hello_interval = struct.unpack("!H", pkt[28:30])[0]
    priority = pkt[31]
    dead_interval = struct.unpack("!I", pkt[32:36])[0]
    dr = ip_from_bytes(pkt[36:40])
    bdr = ip_from_bytes(pkt[40:44])
    neighbors_list = []
    for i in range(44, len(pkt), 4):
        neighbors_list.append(ip_from_bytes(pkt[i:i+4]))
    return {
        "router_id": router_id, "netmask": netmask, "hello_interval": hello_interval,
        "priority": priority, "dead_interval": dead_interval, "dr": dr, "bdr": bdr,
        "neighbors": neighbors_list
    }

def handle_hello(pkt, source_ip):
    hello = parse_hello_packet(pkt)
    if not hello:
        print("Hello mal formado"); return
    rid = hello['router_id']
    if rid not in neighbors:
        neighbors[rid] = {
            "ip": source_ip, "interface": INTERFACES[0], "last_hello": time.time(),
            "state": "Init", "dr": hello["dr"], "bdr": hello["bdr"], "priority": hello["priority"]
        }
        print(f"[👀] Nuevo vecino {rid} en estado Init")
    if ROUTER_ID in hello["neighbors"]:
        if neighbors[rid]["state"] != "2-Way":
            neighbors[rid]["state"] = "2-Way"
            print(f"[🤝] Estado con {rid} → 2-Way (adyacencia posible)")
            dbd_pkt = build_dbd_packet(ROUTER_ID) #,lsa_headers)
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_RAW) as s:
                    s.sendto(dbd_pkt, (source_ip, 0))
                    print(f"[📤] DBD enviado a {source_ip}")
            except Exception as e:
                print(f"[⚠️] Error al enviar DBD a {source_ip}: {e}")
    else:
        print(f"[🟡] Hello recibido de {rid} pero aún no nos reconoce")
    neighbors[rid]["last_hello"] = time.time()