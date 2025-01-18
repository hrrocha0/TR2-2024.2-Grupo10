import sys
from socket import *
from threading import *
import json
import time

HOST = '127.0.0.1'
PORT = 8000

peers = {}
peers_lock = Lock()

def iniciar_tracker() -> None:
    """
    Inicia o tracker para o sistema P2P.
    """
    try:
        servidor_socket = criar_socket(HOST, PORT)
        print(f"Tracker ativo em {HOST}:{PORT}...")

        # Thread para remover peers inativos
        Thread(target=remover_peers_inativos, daemon=True).start()

        while True:
            cliente_socket, endereco_cliente = servidor_socket.accept()
            print(f"Nova conexão de {endereco_cliente}")
            Thread(target=lidar_com_peer, args=(cliente_socket, endereco_cliente)).start()

    except IOError as e:
        print(f"Erro: {e}")
        sys.exit(1)

def criar_socket(host: str, port: int) -> socket:
    """
    Cria um socket TCP de servidor com o endereço e porta especificados.
    """
    servidor_socket = socket(AF_INET, SOCK_STREAM)
    servidor_socket.bind((host, port))
    servidor_socket.listen(5)
    return servidor_socket

def lidar_com_peer(cliente_socket: socket, endereco_cliente: (str, int)) -> None:
    """
    Lida com as requisições de um peer.
    """
    try:
        while True:
            dados = cliente_socket.recv(1024).decode('utf-8')
            if not dados:
                break

            requisicao = json.loads(dados)
            resposta = processar_requisicao(requisicao, endereco_cliente)
            cliente_socket.send(resposta.encode('utf-8'))

    except Exception as e:
        print(f"Erro ao lidar com o peer {endereco_cliente}: {e}")

    finally:
        cliente_socket.close()

def processar_requisicao(requisicao: dict, endereco_cliente: (str, int)) -> str:
    """
    Processa diferentes tipos de requisições do peer.
    """
    match requisicao.get("tipo"):
        case "registro":
            peer_id = requisicao.get("peer_id")
            arquivos = requisicao.get("arquivos", [])
            return lidar_com_registro(peer_id, arquivos, endereco_cliente)

        case "busca":
            nome_arquivo = requisicao.get("nome_arquivo")
            return lidar_com_busca(nome_arquivo)

        case "lista":
            return lidar_com_lista()

        case _:
            return json.dumps({"status": "erro", "mensagem": "Tipo de mensagem desconhecido"})

def lidar_com_registro(peer_id: str, arquivos: list, endereco_cliente: (str, int)) -> str:
    """
    Registra um peer no tracker.
    """
    with peers_lock:
        peers[peer_id] = {
            "endereco": endereco_cliente,
            "arquivos": arquivos,
            "ultima_atividade": time.time(),
        }
    print(f"Peer {peer_id} registrado com arquivos: {arquivos}")
    return json.dumps({"status": "sucesso", "mensagem": "Peer registrado com sucesso"})

def lidar_com_busca(nome_arquivo: str) -> str:
    """
    Busca peers que possuem o arquivo solicitado.
    """
    with peers_lock:
        resultado = [
            {"peer_id": peer_id, "endereco": info_peer["endereco"]}
            for peer_id, info_peer in peers.items()
            if nome_arquivo in info_peer["arquivos"]
        ]
    if resultado:
        print(f"Arquivo '{nome_arquivo}' encontrado nos peers: {resultado}")
        return json.dumps({"status": "sucesso", "peers": resultado})
    else:
        print(f"Arquivo '{nome_arquivo}' não encontrado")
        return json.dumps({"status": "erro", "mensagem": "Arquivo não encontrado"})

def lidar_com_lista() -> str:
    """
    Retorna a lista de todos os peers e seus arquivos.
    """
    with peers_lock:
        lista_peers = {
            peer_id: {"arquivos": info_peer["arquivos"], "endereco": info_peer["endereco"]}
            for peer_id, info_peer in peers.items()
        }
    return json.dumps({"status": "sucesso", "peers": lista_peers})

def remover_peers_inativos() -> None:
    """
    Remove peers inativos da lista global.
    """
    while True:
        with peers_lock:
            tempo_atual = time.time()
            peers_inativos = [
                peer_id
                for peer_id, info_peer in peers.items()
                if tempo_atual - info_peer["ultima_atividade"] > 60
            ]
            for peer_id in peers_inativos:
                del peers[peer_id]
                print(f"Peer {peer_id} removido por inatividade.")
        time.sleep(30)

if __name__ == "__main__":
    iniciar_tracker()
