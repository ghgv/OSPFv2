
import socket, struct, time


#from ospf_daemon.dbd import parse_dbd
from ospf_daemon.lsr import build_lsr_packet
from ospf_daemon.lsdb import lsdb
from ospf_daemon.config import ROUTER_ID, IP_SALIDA
from ospf_daemon.build_ip import build_ip_header
from ospf_daemon.lsr import build_lsr_packet
from ospf_daemon.neighbors import neighbors
#from ospf_daemon.lsdb import lsdb
import array

def ip_to_bytes(ip):
    return socket.inet_aton(ip)

def ip_from_bytes(b): return socket.inet_ntoa(b)

def checksum(data):
    if len(data) % 2 != 0:
        data += b'\0'
    res = sum(array.array("H", data))
    res = (res >> 16) + (res & 0xffff)
    res += res >> 16
    return (~res) & 0xffff

def parse_dbd(pkt):
    if len(pkt) < 32:
        raise Exception("DBD muy corto")

    offset = 32
    headers = []

    while offset + 20 <= len(pkt):
        lsa_header = pkt[offset:offset+20]
        lsa_type = lsa_header[3]
        lsa_id = ip_from_bytes(lsa_header[4:8])
        adv_router = ip_from_bytes(lsa_header[8:12])
        seq_num = struct.unpack("!I", lsa_header[12:16])[0]
        headers.append({
            "type": lsa_type,
            "lsa_id": lsa_id,
            "adv_router": adv_router,
            "seq": seq_num
        })
        print(headers)
        offset += 20

    return headers


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

#def build_dbd_packet(router_id, mtu=1500, opts=0x02, flags=0x07, dd_seq=1):
def build_dbd_packet(router_id, mtu=1500, options=2, flags=0x07, seq=0x80000001, lsa_headers=[], rid=""):
    # === Cuerpo del DBD ===
    body = struct.pack("!HBBI", mtu, options, flags, seq)
    for h in lsa_headers:
        body += struct.pack("!B", 0)  # age
        body += struct.pack("!B", 1)  # options
        body += struct.pack("!B", h['type'])
        body += ip_to_bytes(h['lsa_id'])
        body += ip_to_bytes(h['adv_router'])
        body += struct.pack("!I", h['seq'])
        body += struct.pack("!H", 0)  # checksum
        body += struct.pack("!H", 0)  # length

    # === Cabecera OSPF ===
    version = 2
    type_ = 2
    header = struct.pack("!BBH", version, type_, 0)  # longitud luego
    header += ip_to_bytes(router_id)
    header += ip_to_bytes("0.0.0.0")  # Área
    header += b"\x00\x00"            # checksum
    header += struct.pack("!H", 0)   # AuType
    header += struct.pack("!Q", 0)   # Auth

    pkt = header + body
    length = len(pkt)
    pkt = pkt[:2] + struct.pack("!H", length) + pkt[4:]
    pkt_chk = pkt[:12] + b'\x00\x00' + pkt[14:]
    chksum = checksum(pkt_chk)
    pkt = pkt[:12] + struct.pack("H", chksum) + pkt[14:] #siempre sin ! (no !H)

    # === Agregar cabecera IP ===
    print(rid)
    ip_hdr = build_ip_header(IP_SALIDA, rid ,len(pkt))
    #ip_hdr = build_ip_header(IP_SALIDA, "192.168.3.1", len(pkt))
    return ip_hdr + pkt


def handle_dbd(pkt, source_ip):
    try:
        headers = parse_dbd(pkt)
        missing = []

        for h in headers:
            lsa_id = (h['type'], h['lsa_id'], h['adv_router'])
            if lsa_id not in lsdb.db.items():
                print(f"[📥] Falta LSA {lsa_id}, se solicitará")
                missing.append(h)

        if missing:
            lsr_pkt = build_lsr_packet(missing)
            ip_hdr = build_ip_header(IP_SALIDA, source_ip, len(lsr_pkt))
            pkt = ip_hdr + lsr_pkt
            with socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_RAW) as s:
                s.sendto(pkt, (source_ip, 0))
                print(f"[📤] LSR enviado a {source_ip} con {len(missing)} solicitudes")
        else:
            print("[✔️] Todas las LSAs ya están presentes")
            


    except Exception as e:
        print(f"[⚠️] Error al manejar DBD: {e}")

def send_dbd_periodically():
    sock = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_RAW)
    seq = 0x80000001

    while True:
        # Revisar si hay al menos un vecino en estado 2-Way (simulado como visto en neighbors)
        if neighbors:
            for ip, data in neighbors.items():
                try:
                    lsa_headers = []
                    for (typ, lsa_id, adv), lsa in lsdb.db.items():
                        lsa_headers.append({
                            "type": typ,
                            "lsa_id": lsa_id,
                            "adv_router": adv,
                            "seq": lsa["seq"]
                        })

                    pkt = build_dbd_packet(ROUTER_ID, seq=seq, lsa_headers=lsa_headers, rid=ip)
                    e= sock.sendto(pkt, (ip, 0))
                    print("DBD enviado: ",e)
                    print(f"[📤] DBD enviado a {ip} con {len(lsa_headers)} LSAs (seq={hex(seq)})")
                except Exception as e:
                    print(f"[⚠️] Error enviando DBD a {ip}: {e}")
            seq += 1
        else:
            print("[⏳] Esperando vecinos en estado 2-Way...")

        time.sleep(15)