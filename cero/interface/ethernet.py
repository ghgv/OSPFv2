import socket

def mac_str_to_bytes(mac):
    return bytes.fromhex(mac.replace(':', ''))

def build_ethernet(dst_mac="",src_mac="",ethertype="",payload=""):

    # Rellenar si es muy corto (mínimo tamaño de payload en Ethernet es 46 bytes)
    if len(payload) < 46:
        payload += b"\x00" * (46 - len(payload))
    ethertype=hex(ethertype)
    ethertype = 0x0800             # IPv4
    # Construir el frame
    frame = (
        mac_str_to_bytes(dst_mac) +
        mac_str_to_bytes(src_mac) +
        ethertype.to_bytes(2, 'big') +
        payload
    )

    # Enviar por interfaz
       
    return frame
