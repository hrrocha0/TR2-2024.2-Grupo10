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
        print('1. Buscar arquivos no tracker')
        print('2. iniciar char com outro peer')
        print('3. Listar arquivos no tracker')
        print('4. Listar Peer ativos')
        print('5. Selecionar arquivo para compartilhar')
        print('6. Baixar arquivo')
        print('7. Sair')

        opcao = input('Escolha uma opção: ')

        if opcao == '1':
            resultado = buscar_arquivo()
            if resultado.get('status') == 'sucesso':
                print(f'Arquivo encontrado nos seguintes peers: {resultado.get("peers")}')
            else:
                print(f'Erro: {resultado.get("mensagem")}')

        elif opcao == '2':
<<<<<<< HEAD
            enviar_mensagem(id_peer)

=======
            peer_id_destino = input('Digite o ID do peer para iniciar o chat: ')
            endereco_peer = input('Digite o endereço do peer (IP:PORTA): ').split(':')
            Thread(target=chat_peer, args=(peer_id_destino, endereco_peer[0], int(endereco_peer[1]), id_peer), daemon=True).start()

                
>>>>>>> teste
        elif opcao == '3':
            resultado = obter_lista_peers()
            if resultado.get('status') == 'sucesso':
                arquivos_disponiveis = listar_arquivos_no_peers(resultado.get('peers', {}))
                print(f'Arquivos disponíveis: {arquivos_disponiveis}')
            else:
                print(f'Erro: {resultado.get("mensagem", "Desconhecido")}')

        elif opcao == '4':
            resultado = obter_lista_peers()
            if resultado.get('status') == 'sucesso':
                peers = resultado.get("peers", [])
            if peers:
                print("Peers ativos:")
                for peer_id, peer_info in peers.items():
                    endereco = peer_info.get('endereco', [])
                    if endereco and len(endereco) > 1:
                        ip, porta = endereco[0], endereco[1]
                        print(f"Peer ID: {peer_id} | 127.0.0.1:{porta}")
                    else:
                        print("Peer inválido na lista.")
                else:
                    None
            else:
                print(f'Erro: {resultado.get("mensagem")}')

        elif opcao == '5':
            caminho_arquivo = selecionar_arquivo()
            if caminho_arquivo:
                nome_arquivo = os.path.basename(caminho_arquivo)
                arquivos.append(nome_arquivo)
                print(f'Arquivo "{nome_arquivo}" disponível para outros peers.')

                try:
                    with criar_cliente_socket(HOST_TRACKER, PORTA_TRACKER) as cliente_socket:
                        requisicao = json.dumps({
                            "tipo": "atualizar_arquivos",
                            "id_peer": id_peer,
                            "arquivos": [nome_arquivo]
                        })
                        cliente_socket.send(requisicao.encode('utf-8'))
                        resposta = cliente_socket.recv(1024).decode('utf-8')
                        print(json.loads(resposta).get("ERRO"))
                except Exception as e:
                    print(f"ERRO")

        elif opcao == '6':
            arquivos_disponiveis = obter_lista_arquivos()

            if not arquivos_disponiveis:
                print("Nenhum arquivo disponível")
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

        elif opcao == '7':
            print('Encerrando peer...')
            break

        else:
            print('Erro: operação inexistente')


def selecionar_arquivo():
    root = tk.Tk()
    root.withdraw()

    caminho_arquivo = filedialog.askopenfilename(title="Selecione um arquivo")

    return caminho_arquivo if caminho_arquivo else None


<<<<<<< HEAD
=======
def chat_peer(peer_id_destino: str, host_peer: str, porta_peer: int, id_peer: str) -> None:
    """
    Permite o chat direto entre dois peers.
    :param peer_id_destino: O ID do peer de destino.
    :param host_peer: O IP do peer de destino.
    :param porta_peer: A porta do peer de destino.
    :param id_peer: O ID do peer atual.
    :return: None
    """
    try:
        with socket(AF_INET, SOCK_STREAM) as s:
            s.connect((host_peer, porta_peer))

            s.sendall(json.dumps({"tipo": "chat", "remetente": id_peer, "mensagem": "Conexão estabelecida."}).encode('utf-8'))

            while True:
                dados = s.recv(1024).decode('utf-8')
                if not dados:
                    print("Conexão encerrada pelo peer.")
                    break
                mensagem_recebida = json.loads(dados)
                print(f'{peer_id_destino}: {mensagem_recebida["mensagem"]}')

                mensagem = input(f'{id_peer} (Digite sua mensagem): ')
                if mensagem.lower() == 'sair':
                    print('Saindo do chat...')
                    break
                
                requisicao = json.dumps({'tipo': 'chat', 'mensagem': mensagem, 'remetente': id_peer})
                s.send(requisicao.encode('utf-8'))
                
    except Exception as e:
        print(f'Erro no chat com o peer {peer_id_destino}: {e}')



>>>>>>> teste
def registrar_peer(id_peer: str, arquivos: list[str], porta_peer: int) -> None:
    """
    Registra um peer no tracker.
    :param id_peer: O ID do peer.
    :param arquivos: Os arquivos que o peer possui.
    :param porta_peer: A porta de servidor do peer.
    :return: None
    """
    try:
        with criar_cliente_socket(HOST_TRACKER, PORTA_TRACKER) as cliente_socket:
            requisicao = json.dumps({
                'tipo': 'registro',
                'id_peer': id_peer,
                'arquivos': arquivos,
                'porta': porta_peer
            })
            cliente_socket.send(requisicao.encode('utf-8'))
            resposta = cliente_socket.recv(1024).decode('utf-8')
            if resposta != "sucesso":
                None
    except Exception as e:
        print(f"Erro ao registrar peer: {e}")

<<<<<<< HEAD

def enviar_arquivo(socket_cliente: socket, nome_arquivo: str) -> None:
=======
        
def enviar_arquivo(cliente_socket: socket, nome_arquivo: str) -> None:
>>>>>>> teste
    """
    Envia um arquivo para o peer que solicitou o download.
    :param cliente_socket: Socket do cliente solicitante.
    :param nome_arquivo: Nome do arquivo a ser enviado.
    :return: None
    """
    try:
        with open(nome_arquivo, 'rb') as arquivo:
            cliente_socket.sendall(arquivo.read())
        print(f'Arquivo "{nome_arquivo}" enviado com sucesso.')
    except FileNotFoundError:
        print(f'Erro: Arquivo "{nome_arquivo}" não encontrado.')


def baixar_arquivo():
    """
    Permite ao usuário baixar um arquivo de outro peer, fornecendo apenas o nome do arquivo.
    """
    nome_arquivo = input('Digite o nome do arquivo que deseja baixar: ')
    arquivos_disponiveis = obter_lista_arquivos()

    if nome_arquivo not in arquivos_disponiveis:
        print(f"Erro: Arquivo '{nome_arquivo}' não encontrado no tracker.")
        return

    peers_arquivo = arquivos_disponiveis[nome_arquivo]
    print(f"Arquivo '{nome_arquivo}' encontrado nos seguintes peers:")

    for i, peer in enumerate(peers_arquivo, 1):
        print(f"{i}. ID: {peer['id']} | Porta: {peer['porta']}")

    escolha_peer = input(f"Escolha o número do peer para baixar o arquivo '{nome_arquivo}': ")
    try:
        escolha_peer = int(escolha_peer) - 1
        endereco_peer = ('127.0.0.1', peers_arquivo[escolha_peer]['porta'])
        baixar_arquivo_peer(endereco_peer, nome_arquivo)

    except (ValueError, IndexError):
        print("Escolha inválida. Tente novamente.")


def baixar_arquivo_peer(endereco_peer: tuple, nome_arquivo: str):
    """
    Conecta-se ao peer para baixar o arquivo.
    :param endereco_peer: O endereço do peer.
    :param nome_arquivo: O nome do arquivo a ser baixado.
    """
    try:
        with socket(AF_INET, SOCK_STREAM) as s:
            s.connect(endereco_peer)
            requisicao = json.dumps({'tipo': 'download', 'arquivo': nome_arquivo})
            s.send(requisicao.encode('utf-8'))

            resposta = s.recv(1024).decode('utf-8')
            resposta = json.loads(resposta)

            if resposta.get('status') == 'sucesso':
                print(f"Arquivo '{nome_arquivo}' encontrado. Baixando...")

                with open(nome_arquivo, 'wb') as f:
                    while True:
                        dados = s.recv(1024)
                        if not dados:
                            break
                        f.write(dados)

                print(f"Arquivo '{nome_arquivo}' baixado com sucesso!")
            else:
                print(f"Erro ao baixar o arquivo: {resposta.get('mensagem')}")
    except Exception as e:
        print(f"Erro ao baixar o arquivo do peer: {e}")


def buscar_arquivo() -> dict:
    nome_arquivo = input('Nome do arquivo para buscar: ')
    with (criar_cliente_socket(HOST_TRACKER, PORTA_TRACKER) as cliente_socket):
        requisicao = json.dumps({'tipo': 'busca', 'nome_arquivo': nome_arquivo})
        cliente_socket.send(requisicao.encode('utf-8'))
        resposta = cliente_socket.recv(1024).decode('utf-8')
        return json.loads(resposta) if resposta else {'status': 'erro', 'mensagem': 'Nenhuma resposta do tracker.'}


<<<<<<< HEAD
def enviar_mensagem(id_peer: str) -> None:
    endereco_peer = input('Digite o endereço do peer(IP:PORTA): ').split(':')

    host_peer = endereco_peer[0]
    porta_peer = int(endereco_peer[1])

    while True:
        mensagem = input(f'> ')

        if mensagem == '':
            return

        with criar_socket_cliente(host_peer, porta_peer) as socket_cliente:
            requisicao = json.dumps({'tipo': 'chat', 'mensagem': mensagem, 'remetente': id_peer})
            socket_cliente.send(requisicao.encode('utf-8'))
            resposta = json.loads(socket_cliente.recv(1024).decode('utf-8'))

            if resposta['status'] == 'erro':
                print(f'Erro: {resposta['mensagem']}')
                return


#   endereco_peer = input('Digite o endereço do peer(IP:PORTA): ').split(':')
#
#    try:
#        mensagem = input('Digite sua mensagem: ')
#
#        host_peer = endereco_peer[0]
#        porta_peer = int(endereco_peer[1])
#
#        with criar_socket_cliente(host_peer, porta_peer) as socket_cliente:
#            requisicao = json.dumps({'tipo': 'chat', 'mensagem': mensagem, 'remetente': id_peer})
#            socket_cliente.send(requisicao.encode('utf-8'))
#            resposta = socket_cliente.recv(1024).decode('utf-8')
#
#            return json.loads(resposta) if resposta else {'status': 'erro', 'mensagem': 'Nenhuma resposta do peer.'}

=======
def enviar_mensagem(id_peer: str, host_destino: str, porta_destino: int) -> None:
    """
    Envia mensagens para outro peer.
    :param id_peer: O ID do peer atual.
    :param host_destino: O IP do peer de destino.
    :param porta_destino: A porta do peer de destino.
    :return: None
    """
    try:
        with socket(AF_INET, SOCK_STREAM) as s:
            s.connect((host_destino, porta_destino))
            print(f"{id_peer} conectado ao peer {host_destino}:{porta_destino}")

            while True:
                mensagem = input(f"{id_peer} (Digite sua mensagem ou 'sair' para encerrar): ")
                s.sendall(mensagem.encode('utf-8'))
                if mensagem.lower() == 'sair':
                    break
    except Exception as e:
        print(f"Erro ao enviar mensagem: {e}")
>>>>>>> teste

def obter_lista_peers() -> dict[str, any]:
    with criar_cliente_socket(HOST_TRACKER, PORTA_TRACKER) as cliente_socket:
        requisicao = json.dumps({'tipo': 'listar_peers'})
        cliente_socket.send(requisicao.encode('utf-8'))
        resposta = cliente_socket.recv(1024).decode('utf-8')
        return json.loads(resposta) if resposta else {'status': 'erro', 'mensagem': 'Nenhuma resposta do tracker.'}


def obter_lista_arquivos():
    """
    Obtém a lista de arquivos disponíveis no tracker.
    Retorna um dicionário onde as chaves são os arquivos e os valores são os peers que os possuem.
    """
    try:
        with socket(AF_INET, SOCK_STREAM) as s:
            s.connect((HOST_TRACKER, PORTA_TRACKER))
            mensagem = json.dumps({"tipo": "listar_arquivos"})
            s.send(mensagem.encode('utf-8'))
            resposta = json.loads(s.recv(4096).decode('utf-8'))
            return resposta.get('arquivos', {})
    except Exception as e:
        print(f'Erro ao obter lista de arquivos: {e}')
        return {}


def listar_arquivos_no_peers(peers_encontrados):
    arquivos_disponiveis = {}

    for peer_id, peer_info in peers_encontrados.items():
        for arquivo in peer_info.get("arquivos", []):
            if arquivo not in arquivos_disponiveis:
                arquivos_disponiveis[arquivo] = []

            endereco = peer_info.get("endereco", [])
            porta = endereco[1] if len(endereco) > 1 else "desconhecida"

            arquivos_disponiveis[arquivo].append({
                "id": peer_id,
                "porta": porta
            })

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
        servidor_socket = criar_servidor_socket(HOST_PEER, porta_peer)
        print(f'ID: {id_peer}')
        print(f'Porta: {porta_peer}')

        while True:
            cliente_socket, endereco_cliente = servidor_socket.accept()
            Thread(target=lidar_com_requisicao, args=(cliente_socket, arquivos)).start()

    except IOError as e:
        print(f'Erro: {e}')
        sys.exit(1)

def servidor_chat(id_peer: str, host: str, porta: int) -> None:
    """
    Servidor de chat que aguarda mensagens de outros peers.
    :param id_peer: O ID do peer atual.
    :param host: O IP do peer (geralmente localhost para este caso).
    :param porta: A porta para o servidor de chat.
    :return: None
    """
    try:
        with socket(AF_INET, SOCK_STREAM) as s:
            s.bind((host, porta))
            s.listen(1)  # Aceitar apenas uma conexão por vez.
            print(f'{id_peer} - Servidor de chat iniciado na porta {porta}')
            
            while True:
                cliente_socket, _ = s.accept()
                with cliente_socket:
                    print("Conexão estabelecida com o peer.")
                    while True:
                        mensagem = cliente_socket.recv(1024).decode('utf-8')
                        if not mensagem:
                            break  # Se a conexão for fechada, sai do loop.
                        print(f"Mensagem recebida: {mensagem}")
                        
                        # Aguardando a próxima mensagem
                        if mensagem.lower() == 'sair':
                            print(f"{id_peer} saiu do chat.")
                            break
    except Exception as e:
        print(f"Erro no servidor de chat: {e}")

def lidar_com_requisicao(cliente_socket: socket, arquivos: list[str]) -> None:
    try:
        dados = cliente_socket.recv(1024).decode('utf-8')

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
                cliente_socket.send(json.dumps(resposta).encode('utf-8'))

            case 'listagem':
                resposta = {'status': 'sucesso', 'arquivos': arquivos}

            case 'download':
                nome_arquivo = requisicao.get('arquivo')

                if nome_arquivo in arquivos and os.path.exists(nome_arquivo):
                    with open(nome_arquivo, 'rb') as f:
                        conteudo = f.read()

                    resposta = {'status': 'sucesso', 'mensagem': 'Enviando arquivo.', 'tamanho': len(conteudo)}
                    cliente_socket.send(json.dumps(resposta).encode('utf-8'))

                    cliente_socket.sendall(conteudo)
                    print(f'Arquivo "{nome_arquivo}" enviado com sucesso.')
                else:
                    resposta = {'status': 'erro', 'mensagem': 'Arquivo não encontrado.'}
                    cliente_socket.send(json.dumps(resposta).encode('utf-8'))

            case _:
                resposta = {'status': 'erro', 'mensagem': f'Tipo de mensagem desconhecido: {tipo_requisicao}'}

        if tipo_requisicao != 'download':
            cliente_socket.send(json.dumps(resposta).encode('utf-8'))

    except json.JSONDecodeError:
        print("Erro ao decodificar JSON da requisição.")
    except Exception as e:
        print(f'Erro ao lidar com requisição: {e}')
    finally:
        cliente_socket.close()


if __name__ == '__main__':
    id_peer = input('Digite o ID: ')
    arquivos = []
    porta_peer = int(input('Porta do peer que queira usar: '))
    iniciar_peer(id_peer, arquivos, porta_peer)
