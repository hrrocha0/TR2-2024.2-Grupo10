import socket
import json

HOST = '127.0.0.1'
PORT = 8000

def conectar_ao_tracker():
    """
    Estabelece uma conexão com o tracker e retorna o socket.
    """
    sock_cliente = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock_cliente.connect((HOST, PORT))
    return sock_cliente

def registrar_peer(peer_id, arquivos):
    """
    Registra o peer e seus arquivos no tracker.
    """
    requisicao = {
        "tipo": "registro",
        "peer_id": peer_id,
        "arquivos": arquivos
    }
    sock_cliente = conectar_ao_tracker()
    sock_cliente.send(json.dumps(requisicao).encode('utf-8'))
    
    resposta = sock_cliente.recv(1024).decode('utf-8')
    print(f"Resposta do tracker: {resposta}")
    
    sock_cliente.close()

def buscar_arquivo(nome_arquivo):
    """
    Realiza a busca de um arquivo no tracker.
    """
    requisicao = {
        "tipo": "busca",
        "nome_arquivo": nome_arquivo
    }
    sock_cliente = conectar_ao_tracker()
    sock_cliente.send(json.dumps(requisicao).encode('utf-8'))
    
    resposta = sock_cliente.recv(1024).decode('utf-8')
    print(f"Resultado da busca: {resposta}")
    
    sock_cliente.close()

def main():
    registrar_peer("peer1", ["arquivo1.txt", "video.mp4", "imagem.png"])
    buscar_arquivo("arquivo1.txt")

if __name__ == "__main__":
    main()
