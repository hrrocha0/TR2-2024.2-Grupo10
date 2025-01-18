import sys
from socket import *
from threading import *
import json
import time

HOST = '127.0.0.1'
PORT = 8000

# Dicionário para armazenar os peers registrados
# Formato: {peer_id: {"address": (ip, port), "files": [file1, file2], "last_seen": timestamp}}
__peers = {}

# Lock para evitar problemas de concorrência
peers_lock = Lock()


def main() -> None:
    """
    Tracker para o sistema P2P.
    """
    try:
        server_socket = create_socket(HOST, PORT)
        print(f"Tracker rodando em {HOST}:{PORT}...")

        # Thread para remover peers inativos periodicamente
        Thread(target=remove_inactive_peers, daemon=True).start()

        while True:
            client_socket, client_address = server_socket.accept()
            print(f"Nova conexão de {client_address}")
            Thread(target=handle_peer, args=(client_socket, client_address)).start()

    except IOError as e:
        print(f"Erro: {e}")
        sys.exit(1)


def create_socket(host: str, port: int) -> socket:
    """
    Cria um socket TCP de servidor com o endereço e porta especificados.
    """
    server_socket = socket(AF_INET, SOCK_STREAM)
    server_socket.bind((host, port))
    server_socket.listen(5)
    return server_socket


def handle_peer(client_socket: socket, client_address: (str, int)) -> None:
    """
    Lida com as requisições de um peer.
    """
    try:
        while True:
            data = client_socket.recv(1024).decode('utf-8')
            if not data:
                break

            request = json.loads(data)
            response = process_request(request, client_address)
            client_socket.send(response.encode('utf-8'))

    except Exception as e:
        print(f"Erro ao lidar com o peer {client_address}: {e}")

    finally:
        client_socket.close()


def process_request(request: dict, client_address: (str, int)) -> str:
    """
    Processa diferentes tipos de requisições do peer.
    """
    match request.get("type"):
        case "register":
            peer_id = request.get("peer_id")
            files = request.get("files", [])
            return handle_register(peer_id, files, client_address)

        case "search":
            filename = request.get("filename")
            return handle_search(filename)

        case "list":
            return handle_list()

        case _:
            return json.dumps({"status": "error", "message": "Tipo de mensagem desconhecido"})


def handle_register(peer_id: str, files: list, client_address: (str, int)) -> str:
    """
    Registra um peer no tracker.
    """
    with peers_lock:
        __peers[peer_id] = {
            "address": client_address,
            "files": files,
            "last_seen": time.time(),
        }
    print(f"Peer {peer_id} registrado com arquivos: {files}")
    return json.dumps({"status": "success", "message": "Peer registrado com sucesso"})


def handle_search(filename: str) -> str:
    """
    Busca peers que possuem o arquivo solicitado.
    """
    with peers_lock:
        result = [
            {"peer_id": peer_id, "address": peer_info["address"]}
            for peer_id, peer_info in __peers.items()
            if filename in peer_info["files"]
        ]
    if result:
        print(f"Arquivo '{filename}' encontrado nos peers: {result}")
        return json.dumps({"status": "success", "peers": result})
    else:
        print(f"Arquivo '{filename}' não encontrado")
        return json.dumps({"status": "error", "message": "Arquivo não encontrado"})


def handle_list() -> str:
    """
    Retorna a lista de todos os peers e seus arquivos.
    """
    with peers_lock:
        peer_list = {
            peer_id: {"files": peer_info["files"], "address": peer_info["address"]}
            for peer_id, peer_info in __peers.items()
        }
    return json.dumps({"status": "success", "peers": peer_list})


def remove_inactive_peers() -> None:
    """
    Remove peers inativos da lista global.
    """
    while True:
        with peers_lock:
            current_time = time.time()
            inactive_peers = [
                peer_id
                for peer_id, peer_info in __peers.items()
                if current_time - peer_info["last_seen"] > 60
            ]
            for peer_id in inactive_peers:
                del __peers[peer_id]
                print(f"Peer {peer_id} removido por inatividade.")
        time.sleep(30)


if __name__ == "__main__":
    main()
