import json
import sys
import time

from utilidades_socket import *
from threading import *

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
        else: 
            print('Erro: operação inexistente')


def registrar_peer(id_peer: str, arquivos: list[str], porta_peer: int) -> None:
    """
    Registra um peer no tracker.
    :param id_peer: O ID do peer.
    :param arquivos: Os arquivos que o peer possui.
    :param porta_peer: A porta de servidor do peer.
    :return: None
    """
    with criar_socket_cliente(HOST_TRACKER, PORTA_TRACKER) as socket_cliente:
        requisicao = json.dumps({
            'tipo': 'registro',
            'id_peer': id_peer,
            'arquivos': arquivos,
            'porta': porta_peer
        })
        socket_cliente.send(requisicao.encode('utf-8'))
        resposta = socket_cliente.recv(1024).decode('utf-8')

        print(f'Resposta do tracker: {resposta}')


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

def listar_arquivos_no_peers(peers: dict) -> dict:
    """Lista arquivos disponíveis nos peers."""
    arquivos_disponiveis = {}
    for peer_id, peer_info in peers.items():
        peer_host, peer_port = peer_info['endereco']
        for _ in range(3):
            try:
                with socket(AF_INET, SOCK_STREAM) as s:
                    s.connect((peer_host, peer_port))
                    s.send(json.dumps({'tipo': 'listagem'}).encode('utf-8'))
                    resposta = json.loads(s.recv(1024).decode('utf-8'))
                    if resposta.get("status") == "sucesso":
                        arquivos_disponiveis[peer_id] = resposta.get("arquivos")
                    break  

            except Exception:
                time.sleep(1)

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
            return

        requisicao = json.loads(dados)

        match requisicao.get('tipo'):
            case 'chat':
                mensagem = requisicao.get('mensagem')
                remetente = requisicao.get('remetente')

                print(f'Mensagem recebida de {remetente}: {mensagem}')

                resposta = json.dumps({'status': 'sucesso', 'mensagem': 'Mensagem recebida.'})
                socket_cliente.send(resposta.encode('utf-8'))
            case 'listagem':
                resposta = json.dumps({'status': 'sucesso', 'arquivos': arquivos})
                socket_cliente.send(resposta.encode('utf-8'))
            case _:
                resposta = json.dumps({'status': 'erro', 'mensagem': 'Tipo de mensagem desconhecido.'})
                socket_cliente.send(resposta.encode('utf-8'))

    except Exception as e:
        print(f'Erro ao lidar com requisição: {e}')

    finally:
        socket_cliente.close()


if __name__ == '__main__':
    id_peer = input('Digite o ID: ')
    arquivos = input('Digite os nomes dos arquivos: ').split(',')
    porta_peer = int(input('Porta do peer que queira usar: '))
    iniciar_peer(id_peer, arquivos, porta_peer)