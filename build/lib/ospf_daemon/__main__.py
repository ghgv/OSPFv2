from ospf_daemon.lsa import RouterLSA
from ospf_daemon.lsdb import LSDB
from ospf_daemon.spf import compute_spf
from ospf_daemon.routing import RoutingTable
from ospf_daemon.webviz import iniciar_dashboard
from ospf_daemon.config import ROUTER_ID

import socket, threading, time

lsdb = LSDB()
rt = RoutingTable()

def send_lsa_periodically():
    seq = 0x80000001
    while True:
        vecinos = list(lsdb.db.keys())
        links = [(v, "10.0.0.1", 1, 10) for v in vecinos]
        pkt = RouterLSA(ROUTER_ID, links, seq).build()
        sock = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_RAW)
        sock.sendto(pkt, ("224.0.0.5", 0))
        print(f"[📤] LSA enviado con {len(links)} enlaces")
        seq += 1
        time.sleep(15)

def receive_ospf_packets():
    sock = socket.socket(socket.AF_INET, socket.SOCK_RAW, 89)
    while True:
        data, addr = sock.recvfrom(2048)
        if len(data) < 24:
            continue
        version, tipo = data[0], data[1]
        if version != 2:
            continue
        if tipo == 4:
            lsa_data = data[24:]
            try:
                info = RouterLSA.parse(lsa_data)
                lsdb.add_lsa(info)
                rt.add_interface(info['adv_router'], "eth0")
            except Exception as e:
                print("LSA inválido:", e)

def calcular_rutas():
    while True:
        lsdb.purge_expired()
        rutas = compute_spf(lsdb.get_links(), ROUTER_ID)
        rt.load_from_spf(rutas)
        print("[🧠] Rutas:")
        for dst, info in rutas.items():
            print(f"  {dst} → {info['next_hop']} (costo {info['cost']})")
        time.sleep(10)

def simular_reenvio():
    while True:
        dst = input("Destino: ")
        rt.forward_packet({'dst': dst.strip()})

def main():
    print("[🟢] Daemon OSPF iniciado")
    threading.Thread(target=send_lsa_periodically, daemon=True).start()
    threading.Thread(target=receive_ospf_packets, daemon=True).start()
    threading.Thread(target=calcular_rutas, daemon=True).start()
    iniciar_dashboard(lsdb)
    simular_reenvio()