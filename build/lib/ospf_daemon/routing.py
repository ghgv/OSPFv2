import ipaddress

class RoutingTable:
    def __init__(self):
        self.routes = {}
        self.interfaces = {}

    def load_from_spf(self, spf_table):
        self.routes.clear()
        for dest, info in spf_table.items():
            self.routes[f"{dest}/32"] = (info['next_hop'], info['cost'])

    def add_interface(self, neighbor_ip, iface):
        self.interfaces[neighbor_ip] = iface

    def forward_packet(self, packet):
        dst_ip = packet.get('dst')
        if not dst_ip:
            print("[🚫] Paquete sin destino")
            return
        dst_addr = ipaddress.IPv4Address(dst_ip)
        for route, (next_hop, cost) in self.routes.items():
            net = ipaddress.IPv4Network(route)
            if dst_addr in net:
                iface = self.interfaces.get(next_hop, "??")
                print(f"[📦] Reenviando paquete a {dst_ip} → next hop {next_hop} por interfaz {iface} (costo {cost})")
                return
        print(f"[🛑] No hay ruta para {dst_ip}")