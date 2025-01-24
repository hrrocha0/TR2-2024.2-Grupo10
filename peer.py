from socket import *
import json
from threading import Thread
import time

TRACKER_HOST = '127.0.0.1'
TRACKER_PORT = 8000


def registrar_peer(peer_id, arquivos, peer_port):
    """
    Registra um peer no tracker informando os dados
    
    """
    with socket(AF_INET, SOCK_STREAM) as s:
        s.connect((TRACKER_HOST, TRACKER_PORT))
        mensagem = json.dumps({
            "tipo": "registro",
            "peer_id": peer_id,
            "arquivos": arquivos,
            "peer_port": peer_port
        })
        s.send(mensagem.encode('utf-8'))
        resposta = s.recv(1024).decode('utf-8')
        print("Resposta do tracker:", resposta)


def buscar_arquivo(nome_arquivo):
    """
    Busca um arquivo no tracker informando o nome 

    """
    with socket(AF_INET, SOCK_STREAM) as s:
        s.connect((TRACKER_HOST, TRACKER_PORT))
        mensagem = json.dumps({"tipo": "busca", "nome_arquivo": nome_arquivo})
        s.send(mensagem.encode('utf-8'))
        resposta = s.recv(1024).decode('utf-8')
        if resposta:
            resultado = json.loads(resposta)
            return resultado
        else:
            return {"status": "erro", "mensagem": "Nenhuma resposta do tracker"}

def obter_lista_peers():
    """
    Lista de todos os peers registrados no tracker
    """
    with socket(AF_INET, SOCK_STREAM) as s:
        s.connect((TRACKER_HOST, TRACKER_PORT))
        mensagem = json.dumps({"tipo": "listar_peers"}).encode('utf-8')
        s.send(mensagem)
        resposta = s.recv(1024).decode('utf-8')
        if resposta:
            resultado = json.loads(resposta)
            return resultado
        else:
            return {"status": "erro", "mensagem": "Nenhuma resposta do tracker"}

def servidor_peer(peer_id, arquivos, peer_port):
    """
    Inicia um servidor peer e espera a conexao de outros
    """
    server_socket = socket(AF_INET, SOCK_STREAM)
    server_socket.bind(('127.0.0.1', peer_port))
    server_socket.listen(5)
    print(f"ID:{peer_id} porta:{peer_port}...")

    while True:
        client_socket, client_address = server_socket.accept()
        Thread(target=lidar_com_requisicao, args=(client_socket, arquivos)).start()


def lidar_com_requisicao(client_socket, arquivos):
    """
    Requisição recebida de outros peers
    """
    try:
        dados = client_socket.recv(1024).decode('utf-8')
        requisicao = json.loads(dados)

        if requisicao.get("tipo") == "chat":
            mensagem = requisicao.get("mensagem", "")
            print(f"Mensagem recebida de {requisicao.get('remetente')}: {mensagem}")
            client_socket.send(json.dumps({"status": "ok", "mensagem": "Mensagem recebida"}).encode('utf-8'))
            
        elif requisicao.get("tipo") == "listagem":
            client_socket.send(json.dumps({"status": "ok", "arquivos": arquivos}).encode('utf-8'))

    except Exception as e:
        print(f"Erro ao lidar com requisição: {e}")
        
    finally:
        client_socket.close()


def enviar_arquivo(client_socket, nome_arquivo):
    """
    Envia o conteúdo de um arquivo solicitado para o peer
    """
    try:
        with open(nome_arquivo, 'rb') as f:
            while chunk := f.read(1024):
                client_socket.send(chunk)
        print(f"Arquivo '{nome_arquivo}' enviado com sucesso!")
    except FileNotFoundError:
        mensagem = json.dumps({"status": "erro", "mensagem": "Arquivo não encontrado"}).encode('utf-8')
        client_socket.send(mensagem)


def listar_arquivos_no_peers(peers):
    """
    Lista de todos os arquivos disponiveis
    """
    arquivos_disponiveis = {}
    for peer_id, peer_info in peers.items():
        peer_host, peer_port = peer_info['endereco']
        for _ in range(3):  
            try:
                with socket(AF_INET, SOCK_STREAM) as s:
                    s.connect((peer_host, peer_port))
                    mensagem = json.dumps({"tipo": "listagem"}).encode('utf-8')
                    s.send(mensagem)
                    resposta = s.recv(1024).decode('utf-8')
                    resultado = json.loads(resposta)
                    if resultado.get("status") == "ok":
                        arquivos_disponiveis[peer_id] = resultado.get("arquivos")
                    break  
            except Exception:
                print(f"Erro ao listar arquivos") 
                time.sleep(1) 
    return arquivos_disponiveis


def iniciar_peer(peer_id, arquivos, peer_port):
    """
    Inicia o peer e registra no tracker
    """
    registrar_peer(peer_id, arquivos, peer_port)

    Thread(target=servidor_peer, args=(peer_id, arquivos, peer_port), daemon=True).start()

    while True:
        print("\n1. Buscar arquivo")
        print("2. Enviar mensagem para outro peer")
        print("3. Listar arquivos")
        print("4. Sair")
        opcao = input("Escolha uma opção: ")

        if opcao == "1":
            nome_arquivo = input("Nome do arquivo para buscar: ")
            resultado = buscar_arquivo(nome_arquivo)
            if resultado.get("status") == "sucesso":
                print(f"Arquivo encontrado nos seguintes peers: {resultado['peers']}")
            else:
                print("Arquivo não encontrado.")
                
        elif opcao == "2":
            endereco_peer = input("Digite o endereço do peer (IP:PORTA): ")
            ip, porta = endereco_peer.split(':')
            mensagem = input("Digite sua mensagem: ")
            enviar_mensagem((ip, int(porta)), mensagem, peer_id)

        elif opcao == "3":
            resultado_peers = obter_lista_peers()
            if resultado_peers.get("status") == "sucesso":
                peers = resultado_peers["peers"]
                arquivos = listar_arquivos_no_peers(peers)
                print("\nArquivos disponíveis em todos os peers:", arquivos)
            else:
                print("Erro ao obter lista de peers.")

        elif opcao == "4":
            print("Encerrando peer...")
            break

def enviar_mensagem(peer_endereco, mensagem, remetente):
    """
    Envia mensagem para o chat de outro peer
    """
    peer_host, peer_port = peer_endereco
    with socket(AF_INET, SOCK_STREAM) as s:
        try:
            s.connect((peer_host, peer_port))
            mensagem_chat = json.dumps({"tipo": "chat", "mensagem": mensagem, "remetente": remetente})
            s.send(mensagem_chat.encode('utf-8'))
            resposta = s.recv(1024).decode('utf-8')
            print("Resposta do peer:", resposta)
        except Exception:
            print(f"Erro ao enviar mensagem para {peer_endereco}")


if __name__ == "__main__":
    peer_id = input("Digite o ID: ")
    arquivos = input("Digite o nome do arquivo: ").split(',')
    peer_port = int(input("Porta do peer que queira usar:"))
    iniciar_peer(peer_id, arquivos, peer_port)