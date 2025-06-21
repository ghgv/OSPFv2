from ospf_daemon.lsa import RouterLSA
from ospf_daemon.lsdb import LSDB,lsdb
from ospf_daemon.spf import compute_spf
from ospf_daemon.dbd import handle_dbd,send_dbd_periodically
from ospf_daemon.routing import RoutingTable
from ospf_daemon.webviz import iniciar_dashboard
from ospf_daemon.hello import send_hello_periodically
from ospf_daemon.config import ROUTER_ID
from ospf_daemon.hello import handle_hello
from ospf_daemon.cli import cli


import socket, threading, time

#lsdb = LSDB()
#lsdb = LSDB()

rt = RoutingTable()

def send_lsa_periodically():
    seq = 0x80000001
    while True:
        vecinos = list(lsdb.db.keys())
        links = [(v, "192.168.3.3", 1, 10) for v in vecinos]
        pkt = RouterLSA(ROUTER_ID, links, seq).build()
        sock = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_RAW)
        sock.sendto(pkt, ("224.0.0.5", 0))
        print(f"LSA enviado con {len(links)} enlaces")
        seq += 1
        time.sleep(15)

def receive_ospf_packets():
    # Captura a nivel de enlace
    sock = socket.socket(socket.AF_PACKET, socket.SOCK_RAW, socket.ntohs(0x0800))
    sock.bind(('enp4s0', 0))
    print("Receive OSPF packets started (AF_PACKET)")
    
    while True:
        raw_data, addr = sock.recvfrom(65535)
        print("Paquete recibido")

        # Saltar cabecera Ethernet (14 bytes) y tomar IP
        eth_length = 14
        ip_header = raw_data[eth_length:eth_length+20]
        proto = ip_header[9]

        if proto == 89:  # OSPF
            ospf_packet = raw_data[eth_length+20:]
            version = ospf_packet[0]
            tipo = ospf_packet[1]
            print(f"OSPF tipo {tipo} recibido de {addr}")
            #if len(ospf_packet) < 24:
            #    continue
            version, tipo = ospf_packet[0], ospf_packet[1]
            print("OSPF version" ,version, "tipo", tipo )
            if version != 2:
                continue
            if tipo == 1:  # Tipo Hello
                vecino = addr[0]
                print(f"[💬] Hello recibido en interfaz {vecino}")
                rt.add_interface(vecino, "enp4s0")  # Se asume 'eth0' como interfaz
                src_ip = ".".join(map(str, raw_data[26:30]))
                handle_hello(ospf_packet, src_ip)
                # Aquí podrías también guardar tiempo del último hello recibido
            if tipo == 2:  # Tipo DB description
                vecino = addr[0]
                print(f"[💬] DB description  recibido en interfaz {vecino}.")
                rt.add_interface(vecino, "enp4s0")  # Se asume 'eth0' como interfaz
                src_ip = ".".join(map(str, raw_data[26:30]))
                handle_dbd(ospf_packet, src_ip)
                # Aquí podrías también guardar tiempo del último hello recibido
            if tipo == 4: #Tipo LSA Update
                lsa_data = ospf_packet[24:]
                print(f"[💬] Received LSA 4 ")
                try:
                    info = RouterLSA.parse(lsa_data)
                    #print("info:->",info)
                    lsdb.add_lsa(info)
                    rt.add_interface(info['adv_router'], "enp4s0")
                except Exception as e:
                    print("LSA inválido:", e)

def calcular_rutas():
    while True:
        print("LSDB->",lsdb.db)
        #lsdb.purge_expired()
        print("LSDB--->",lsdb.db)
        rutas = compute_spf(lsdb.get_links(), "2.2.2.2")
        print("rutas",rutas)
        rt.load_from_spf(rutas)
        print("Rutas:")
        for dst, info in rutas.items():
            print(f"  {dst} → {info['next_hop']} (costo {info['cost']})")
        time.sleep(10)

def simular_reenvio():
    while True:
        dst = input("Destino: ")
        rt.forward_packet({'dst': dst.strip()})

def main():
    print("Daemon OSPF iniciado")
    threading.Thread(target=send_lsa_periodically, daemon=True).start()
    threading.Thread(target=send_hello_periodically, daemon=True).start()
    threading.Thread(target=receive_ospf_packets, daemon=True).start()
    threading.Thread(target=calcular_rutas, daemon=True).start()
    threading.Thread(target=send_dbd_periodically, daemon=True).start()
    threading.Thread(target=cli, daemon=True).start()
    iniciar_dashboard(lsdb)
    simular_reenvio()

if __name__ == "__main__":
    main()
    