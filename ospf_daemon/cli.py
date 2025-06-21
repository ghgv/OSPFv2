import socket
import json
from ospf_daemon.lsdb import lsdb
from ospf_daemon.neighbors import neighbors

def handle_command(command):
    tokens = command.strip().split()
    if not tokens:
        return

    cmd = tokens[0]
    args = tokens[1:]

    if cmd == "init":
        if len(args) != 1:
            print("Uso: init <interfaz>")
        else:
            print(f"Inicializando OSPF en interfaz: {args[0]}")
    
    elif cmd == "show":
        print(lsdb.db)
        return lsdb.db
    
    elif cmd == "neig":
        return neighbors
    
    elif cmd == "show":
        print("Mostrando base de datos LSDB...")
    
    elif cmd in ("exit", "quit"):
        print("Saliendo.")
        exit(0)
    
    else:
        print(f"Comando desconocido: {cmd}")

def cli():

    # Crear socket servidor
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(("127.0.0.1", 9000))
    server.listen(1)
    print("Esperando conexión en puerto 9000...")
    conn, addr = server.accept()
    print(f"Conectado desde {addr}")

    # Loop de comandos
    with conn:
        conn.sendall(b"CLI OSPF conectada. Usa 'exit' para salir.\n> ")
        while True:
            data = conn.recv(1024).decode().strip()
            data = handle_command(data)
            response = f"{json.dumps(data,indent=4)}\n> "
            conn.sendall(response.encode())
