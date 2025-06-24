import socket
import struct
from interface.mac import get_mac_address
from interface.ip import build_ip_packet
from interface.ethernet import build_ethernet
from interface.ospf import build_ospf_hello
from config import INTERFACE,SRC_IP,ROUTER_ID,AREA_ID,ALL_SFP_ROUTERS
from db import neigborgs



# Interfaz que deseas escuchar (debe estar activa)

src_mac = get_mac_address(INTERFACE)


# Crear socket RAW tipo AF_PACKET (nivel Ethernet)
sock = socket.socket(socket.AF_PACKET, socket.SOCK_RAW, socket.htons(0x0800))
sock.bind((INTERFACE, 0))

print("📡 Escuchando OSPF en", INTERFACE)

def ip_str(b):
    return ".".join(map(str, b))

while True:
    packet = sock.recv(2048)


    eth_type = struct.unpack('!H', packet[12:14])[0]
    print(hex(eth_type))
    if eth_type != 0x0800:
        continue  # no es IP

    ip_header = packet[14:34]
    ip_fields = struct.unpack('!BBHHHBBH4s4s', ip_header)
    
    proto = ip_fields[6]
    
    if proto != 89:
        continue  # no es OSPF

    src_ip = ip_str(ip_fields[8])
    dst_ip = ip_str(ip_fields[9])
    ospf_data = packet[34:]

    if len(ospf_data) < 24:
        continue  # paquete OSPF muy corto

    version, msg_type, pkt_len = struct.unpack('!BBH', ospf_data[:4])
    router_id = ip_str(ospf_data[4:8])

    print(f"\n📥 OSPF tipo {msg_type} desde {src_ip} → {dst_ip} (Router ID {router_id})")

    if router_id not in neigborgs:
        neigborgs.append(router_id)
    print(neigborgs)

    if dst_ip == "224.0.0.5":
        print("  🟢 Multicast (AllSPFRouters)")
    else:
        print("  🔵 Unicast")

    # Tipos OSPF
    tipos = {
        1: "Hello",
        2: "DB Description",
        3: "LS Request",
        4: "LS Update",
        5: "LS Ack"
    }
    print("  📌 Tipo OSPF:", tipos.get(msg_type, "Desconocido"))
    ospf_data = build_ospf_hello(ROUTER_ID,AREA_ID)
    ip= build_ip_packet(dst_ip=ALL_SFP_ROUTERS,src_ip=SRC_IP,proto=89,payload=ospf_data)
    eth = build_ethernet(dst_mac="ff:ff:ff:ff:ff:ff",src_mac=src_mac,payload=ip,ethertype=0x800)
    
    sock.send(eth)
    
