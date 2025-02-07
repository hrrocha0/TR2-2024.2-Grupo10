import json
import sys
import socket
from utilidades_socket import *
from threading import *
import os
import tkinter as tk
from tkinter import filedialog

HOST_PEER = '127.0.0.1'
HOST_TRACKER = '127.0.0.1'
PORTA_TRACKER = 8001

def iniciar_peer(id_peer: str, arquivos: list[str], porta_peer: int) -> None:
    """
    Inicia o peer do sistema P2P.
    :param id_peer: O ID do peer.
    :param arquivos: Os arquivos que o peer possui.
    :param porta_peer: A porta de servidor do peer.
    :return: None
    """
    if arquivos is None:
        arquivos = []
    registrar_peer(id_peer, arquivos, porta_peer)
    Thread(target=servidor_peer, args=(id_peer, arquivos, porta_peer), daemon=True).start()
    cliente_peer(id_peer, arquivos, porta_peer)


def cliente_peer(id_peer: str, arquivos: list[str], porta_peer: int) -> None:
    """
    Faz requisições a outros peers e ao tracker.
    :param id_peer: O ID do peer.
    :param arquivos: Os arquivos que o peer possui.
    :param porta_peer: A porta de servidor do peer.
    :return: None
    """
    registrar_peer(id_peer, arquivos, porta_peer)

    while True:
        print('Selecione uma opção:')
        print('1. Buscar arquivo')
        print('2. Enviar mensagem para outro peer')
        print('3. Listar arquivos')
        print('4. Sair')
        print('5. Listar Peer')
        print('6. Selecionar arquivo')
        print('7. Baixar arquivo')

        opcao = input('Escolha uma opção: ')

        if opcao == '1':
            resultado = buscar_arquivo()
            if resultado.get('status') == 'sucesso':
                print(f'Arquivo encontrado nos seguintes peers: {resultado.get("peers")}')
            else:
                print(f'Erro: {resultado.get("mensagem")}')
        elif opcao == '2':
            resultado = enviar_mensagem(id_peer)
            if resultado.get('status') == 'sucesso':
               print(f'Resposta do peer: {resultado.get("mensagem")}')
            else:
                print(f'Erro: {resultado.get("mensagem")}')
        elif opcao == '3':
            resultado = obter_lista_peers()
            if resultado.get('status') == 'sucesso':
                arquivos_disponiveis = listar_arquivos_no_peers(resultado.get('peers', {}))
                print(f'Arquivos disponíveis: {arquivos_disponiveis}')
            else:
                print(f'Erro: {resultado.get("mensagem", "Desconhecido")}')
        elif opcao == '4':
            print('Encerrando peer...')
            break

        elif opcao == '5':
            resultado = obter_lista_peers()
            if resultado.get('status') == 'sucesso':
                peers = resultado.get("peers", [])
                if peers:
                    print("Peers ativos:")
                    for peer in peers:
                        if isinstance(peer, (str, int)):
                            print(f"Peer ID: {peer}")
                        else:
                            print("Peer inválido na lista.")
                else:
                    print("Nenhum peer ativo encontrado.")
            else:
                print(f'Erro: {resultado.get("mensagem")}')

        elif opcao == '6':
            caminho_arquivo = selecionar_arquivo()
            if caminho_arquivo:
                nome_arquivo = os.path.basename(caminho_arquivo)
                arquivos.append(nome_arquivo) 
                print(f'Arquivo "{nome_arquivo}" agora está disponível para outros peers.')


        elif opcao == '7':
            arquivos_disponiveis = obter_lista_arquivos()

            if not arquivos_disponiveis:
                print("Nenhum arquivo disponível para download.")
                continue

            print("\nArquivos disponíveis para download:")
            for i, (arquivo, peers) in enumerate(arquivos_disponiveis.items(), 1):
                peer_info = ", ".join([f"{peer['id']} (porta {peer['porta']})" for peer in peers])
                print(f"{i}. {arquivo} - Peers: {peer_info}")

            escolha = input("Escolha o número do arquivo que deseja baixar: ")

            try:
                escolha = int(escolha) - 1
                nome_arquivo = list(arquivos_disponiveis.keys())[escolha]
                peers_arquivo = arquivos_disponiveis[nome_arquivo]

                print("\nPeers que possuem este arquivo:")
                for j, peer in enumerate(peers_arquivo, 1):
                    print(f"{j}. ID: {peer['id']} - Porta: {peer['porta']}")

                escolha_peer = input("Escolha o número do peer para baixar o arquivo: ")
                escolha_peer = int(escolha_peer) - 1
                endereco_peer = ('localhost', peers_arquivo[escolha_peer]['porta'])

                baixar_arquivo(endereco_peer, nome_arquivo)

            except (ValueError, IndexError):
                print("Escolha inválida. Tente novamente.")

        else: 
            print('Erro: operação inexistente')


def baixar_arquivo():
    """
    Permite ao usuário baixar um arquivo de outro peer.
    """
    resultado = obter_lista_peers()
    if resultado.get('status') != 'sucesso':
        print(f'Erro: {resultado.get("mensagem")}')
        return

    peers = resultado.get('peers', {})
    arquivos_disponiveis = listar_arquivos_no_peers(peers)

    if not arquivos_disponiveis:
        print('Nenhum arquivo disponível para download.')
        return

    print('Arquivos disponíveis para download:')
    for idx, (arquivo, peer_info) in enumerate(arquivos_disponiveis.items(), start=1):
        print(f'{idx}. {arquivo} - Peer {peer_info["id"]} (Porta {peer_info["porta"]})')

    escolha = input('Digite o número do arquivo que deseja baixar: ')
    try:
        escolha_idx = int(escolha) - 1
        arquivo_escolhido, peer_info = list(arquivos_disponiveis.items())[escolha_idx]
    except (ValueError, IndexError):
        print('Opção inválida.')
        return

    id_peer = peer_info["id"]
    porta_peer = peer_info["porta"]

    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((HOST_PEER, porta_peer))
            requisicao = json.dumps({'tipo': 'download', 'arquivo': arquivo_escolhido})
            s.send(requisicao.encode('utf-8'))

            with open(arquivo_escolhido, 'wb') as f:
                while True:
                    dados = s.recv(1024)
                    if not dados:
                        break
                    f.write(dados)

        print(f'Arquivo "{arquivo_escolhido}" baixado com sucesso!')

    except Exception as e:
        print(f'Erro ao baixar arquivo: {e}')



def selecionar_arquivo():
    root = tk.Tk()
    root.withdraw()  

    caminho_arquivo = filedialog.askopenfilename(title="Selecione um arquivo")  

    return caminho_arquivo if caminho_arquivo else None

def registrar_peer(id_peer: str, arquivos: list[str], porta_peer: int) -> None:
    """
    Registra um peer no tracker.
    :param id_peer: O ID do peer.
    :param arquivos: Os arquivos que o peer possui.
    :param porta_peer: A porta de servidor do peer.
    :return: None
    """
    try:
        with criar_socket_cliente(HOST_TRACKER, PORTA_TRACKER) as socket_cliente:
            requisicao = json.dumps({
                'tipo': 'registro',
                'id_peer': id_peer,
                'arquivos': arquivos,
                'porta': porta_peer
            })
            socket_cliente.send(requisicao.encode('utf-8'))
            resposta = socket_cliente.recv(1024).decode('utf-8')
            if resposta != "sucesso":
                None             
    except Exception as e:
        None
        
def enviar_arquivo(socket_cliente: socket, nome_arquivo: str) -> None:
    """
    Envia um arquivo para o peer que solicitou o download.
    :param socket_cliente: Socket do cliente solicitante.
    :param nome_arquivo: Nome do arquivo a ser enviado.
    :return: None
    """
    try:
        with open(nome_arquivo, 'rb') as arquivo:
            socket_cliente.sendall(arquivo.read())
        print(f'Arquivo "{nome_arquivo}" enviado com sucesso.')
    except FileNotFoundError:
        print(f'Erro: Arquivo "{nome_arquivo}" não encontrado.')

def baixar_arquivo(endereco_peer: tuple, nome_arquivo: str) -> None:
    try:
        socket_peer = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        socket_peer.connect(endereco_peer)

        requisicao = json.dumps({'tipo': 'download', 'nome_arquivo': nome_arquivo})
        socket_peer.send(requisicao.encode('utf-8'))

        with open(f"baixado_{nome_arquivo}", 'wb') as arquivo:
            while True:
                dados = socket_peer.recv(1024)
                if not dados:
                    break
                arquivo.write(dados)

        print(f'Arquivo "{nome_arquivo}" baixado com sucesso de {endereco_peer}.')
    except Exception as e:
        print(f'Erro ao baixar arquivo: {e}')
    finally:
        socket_peer.close()


def baixar_arquivo_peer(tracker_socket: socket) -> None:
    """
    Lista os arquivos disponíveis e permite que o usuário escolha um para baixar.
    :param tracker_socket: Socket conectado ao tracker.
    :return: None
    """
    try:

        requisicao = json.dumps({'tipo': 'listar_arquivos'})
        tracker_socket.send(requisicao.encode('utf-8'))
        
        resposta = tracker_socket.recv(4096).decode('utf-8')
        arquivos_disponiveis = json.loads(resposta)

        if not arquivos_disponiveis:
            print("Nenhum arquivo disponível para download.")
            return

        print("\nArquivos disponíveis:")
        for idx, (arquivo, peers) in enumerate(arquivos_disponiveis.items()):
            print(f"{idx + 1}. {arquivo} - Disponível em {[(p['id'], p['porta']) for p in peers]}")


        escolha = int(input("\nDigite o número do arquivo que deseja baixar: ")) - 1
        if escolha < 0 or escolha >= len(arquivos_disponiveis):
            print("Escolha inválida!")
            return
        
        nome_arquivo = list(arquivos_disponiveis.keys())[escolha]
        peers_disponiveis = arquivos_disponiveis[nome_arquivo]


        print("\nPeers disponíveis para o arquivo:")
        for idx, peer in enumerate(peers_disponiveis):
            print(f"{idx + 1}. ID: {peer['id']} | Porta: {peer['porta']}")

        escolha_peer = int(input("\nDigite o número do peer para baixar o arquivo: ")) - 1
        if escolha_peer < 0 or escolha_peer >= len(peers_disponiveis):
            print("Escolha inválida!")
            return

        peer_escolhido = peers_disponiveis[escolha_peer]
        endereco_peer = ("127.0.0.1", peer_escolhido['porta'])

        baixar_arquivo_peer(endereco_peer, nome_arquivo)

    except Exception as e:
        print(f"Erro ao baixar arquivo: {e}")


def buscar_arquivo() -> dict:
    nome_arquivo = input('Nome do arquivo para buscar: ')
    with (criar_socket_cliente(HOST_TRACKER, PORTA_TRACKER) as socket_cliente):
        requisicao = json.dumps({'tipo': 'busca', 'nome_arquivo': nome_arquivo})
        socket_cliente.send(requisicao.encode('utf-8'))
        resposta = socket_cliente.recv(1024).decode('utf-8')
        return json.loads(resposta) if resposta else {'status': 'erro', 'mensagem': 'Nenhuma resposta do tracker.'}

def enviar_mensagem(id_peer: str) -> dict[str, any]:
    endereco_peer = input('Digite o endereço do peer(IP:PORTA): ').split(':')
    mensagem = input('Digite sua mensagem: ')

    host_peer = endereco_peer[0]
    porta_peer = int(endereco_peer[1])

    with criar_socket_cliente(host_peer, porta_peer) as socket_cliente:
        requisicao = json.dumps({'tipo': 'chat', 'mensagem': mensagem, 'remetente': id_peer})
        socket_cliente.send(requisicao.encode('utf-8'))
        resposta = socket_cliente.recv(1024).decode('utf-8')

        return json.loads(resposta) if resposta else {'status': 'erro', 'mensagem': 'Nenhuma resposta do peer.'}

def obter_lista_peers() -> dict[str, any]:
    with criar_socket_cliente(HOST_TRACKER, PORTA_TRACKER) as socket_cliente:
        requisicao = json.dumps({'tipo': 'listar_peers'})
        socket_cliente.send(requisicao.encode('utf-8'))
        resposta = socket_cliente.recv(1024).decode('utf-8')
        return json.loads(resposta) if resposta else {'status': 'erro', 'mensagem': 'Nenhuma resposta do tracker.'}

    
def obter_lista_arquivos():
    """
    Obtém a lista de arquivos disponíveis no tracker.
    Retorna um dicionário onde as chaves são os arquivos e os valores são os peers que os possuem.
    """
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((HOST_TRACKER, PORTA_TRACKER))
            mensagem = json.dumps({"tipo": "listar_arquivos"})
            s.send(mensagem.encode('utf-8'))
            resposta = json.loads(s.recv(4096).decode('utf-8'))
            return resposta.get('arquivos', {})
    except Exception as e:
        print(f'Erro ao obter lista de arquivos: {e}')
        return {}

def listar_arquivos_no_peers(peers):
    arquivos_disponiveis = {}

    if not isinstance(peers, dict):
        print("Erro: Estrutura de peers inválida, esperado um dicionário.")
        return {}

    for peer_id, peer_info in peers.items():
        print(f"Verificando peer {peer_id} com informações {peer_info}")  
        if "arquivos" in peer_info:
            arquivos = peer_info.get("arquivos", [])
            print(f"Arquivos disponíveis no peer {peer_id}: {arquivos}") 
            for arquivo in arquivos:
                if arquivo not in arquivos_disponiveis:
                    arquivos_disponiveis[arquivo] = []
                arquivos_disponiveis[arquivo].append({"id": peer_id, "porta": peer_info["porta"]})

    return arquivos_disponiveis



def servidor_peer(id_peer: str, arquivos: list[str], porta_peer: int) -> None:
    """
    Processa as requisições de outros peers.
    :param id_peer: O ID do peer.
    :param arquivos: Os arquivos que o peer possui.
    :param porta_peer: A porta de servidor do peer.
    :return: None
    """
    try:
        socket_servidor = criar_socket_servidor(HOST_PEER, porta_peer)
        print(f'ID: {id_peer}')
        print(f'Porta: {porta_peer}')

        while True:
            socket_cliente, endereco_cliente = socket_servidor.accept()
            Thread(target=lidar_com_requisicao, args=(socket_cliente, arquivos)).start()

    except IOError as e:
        print(f'Erro: {e}')
        sys.exit(1)


def lidar_com_requisicao(socket_cliente: socket, arquivos: list[str]) -> None:
    try:
        dados = socket_cliente.recv(1024).decode('utf-8')

        if not dados:
            print("Conexão fechada pelo cliente.")
            return

        requisicao = json.loads(dados)
        tipo_requisicao = requisicao.get('tipo')

        match tipo_requisicao:
            case 'chat':
                mensagem = requisicao.get('mensagem')
                remetente = requisicao.get('remetente')

                print(f'Mensagem recebida de {remetente}: {mensagem}')
                resposta = {'status': 'sucesso', 'mensagem': 'Mensagem recebida.'}

            case 'listagem':
                resposta = {'status': 'sucesso', 'arquivos': arquivos}

            case 'download':
                nome_arquivo = requisicao.get('arquivo')

                if nome_arquivo in arquivos and os.path.exists(nome_arquivo):
                    with open(nome_arquivo, 'rb') as f:
                        conteudo = f.read()

                    resposta = {'status': 'sucesso', 'mensagem': 'Enviando arquivo.', 'tamanho': len(conteudo)}
                    socket_cliente.send(json.dumps(resposta).encode('utf-8'))

                    socket_cliente.sendall(conteudo)
                    print(f'Arquivo "{nome_arquivo}" enviado com sucesso.')
                else:
                    resposta = {'status': 'erro', 'mensagem': 'Arquivo não encontrado.'}
                    socket_cliente.send(json.dumps(resposta).encode('utf-8'))

            case _:
                resposta = {'status': 'erro', 'mensagem': f'Tipo de mensagem desconhecido: {tipo_requisicao}'}

        if tipo_requisicao != 'download':
            socket_cliente.send(json.dumps(resposta).encode('utf-8'))

    except json.JSONDecodeError:
        print("Erro ao decodificar JSON da requisição.")
    except Exception as e:
        print(f'Erro ao lidar com requisição: {e}')
    finally:
        socket_cliente.close()

if __name__ == '__main__':
    id_peer = input('Digite o ID: ')
    arquivos = []
    porta_peer = int(input('Porta do peer que queira usar: '))
    iniciar_peer(id_peer, arquivos, porta_peer)
