import json
import sys
import time

from utilidades_socket import *
from threading import *

HOST_TRACKER = '127.0.0.1'
PORTA_TRACKER = 8000

peers = {}
mutex_peers = Lock()


def iniciar_tracker(host: str, porta: int) -> None:
    """
    Inicia o tracker para o sistema P2P.
    :return: None
    """
    try:
        socket_servidor = criar_socket_servidor(host, porta)
        print(f'Tracker ativo em {host}:{porta}...')

        Thread(target=remover_peers_inativos, daemon=True).start()

        while True:
            socket_cliente, endereco_cliente = socket_servidor.accept()
            print(f'Nova conexão de {endereco_cliente[0]}:{endereco_cliente[1]}.')

            Thread(target=lidar_com_peer, args=(socket_cliente, endereco_cliente)).start()

    except Exception as e:
        print(f'Erro: {e}')
        sys.exit(1)


def lidar_com_peer(socket_peer: socket, endereco_peer: tuple[str, int]) -> None:
    """
    Gerencia as comunicações entre tracker e peer.
    :param socket_peer: O socket do peer.
    :param endereco_peer: O endereço do peer.
    :return: None
    """
    try:
        dados = socket_peer.recv(1024).decode('utf-8')

        if not dados:
            socket_peer.close()
            return

        requisicao = json.loads(dados)
        porta_peer = requisicao.get('porta', socket_peer.getpeername()[1])
        resposta = processar_requisicao(requisicao, endereco_peer, porta_peer)

        socket_peer.send(resposta.encode('utf-8'))

    except Exception as e:
        print(f'Erro ao lidar com peer {endereco_peer}: {e}')

    finally:
        socket_peer.close()


def processar_requisicao(requisicao: dict[str, any], endereco_peer: tuple[str, int], porta_peer: int) -> str:
    """
    Processa a requisição de um peer.
    :param requisicao: A requisição do peer.
    :param endereco_peer: O endereço do peer.
    :param porta_peer: A porta de servidor do peer.
    :return: A mensagem de resposta.
    """
    operacoes = {
        'registro': lidar_com_registro,
        'busca': lidar_com_busca,
        'listar_peers': lidar_com_lista,
    }
    tipo = requisicao.get('tipo')

    if tipo not in operacoes:
        return json.dumps({'status': 'erro', 'mensagem': 'Tipo de mensagem desconhecido.'})

    return operacoes[tipo](requisicao, endereco_peer, porta_peer)


def lidar_com_registro(requisicao: dict[str, any], endereco_peer: tuple[str, int], porta_peer: int) -> str:
    """
    Registra um peer no tracker.
    :param requisicao: A requisição de registro do peer.
    :param endereco_peer: O endereço do peer.
    :param porta_peer: A porta de servidor do peer.
    :return: A mensagem de resposta.
    """
    id_peer = requisicao.get('id_peer')
    arquivos = requisicao.get('arquivos', [])

    with mutex_peers:
        peers[id_peer] = {
            'endereco': (endereco_peer[0], porta_peer),
            'arquivos': arquivos,
            'ultima_atividade': time.time(),
            'score': 0,
        }
    print(f'Peer {id_peer} registrado com arquivos: {arquivos} e porta: {porta_peer}')

    return json.dumps({'status': 'sucesso', 'mensagem': 'Peer registrado com sucesso.'})


def lidar_com_busca(requisicao: dict[str, any], endereco_peer: tuple[str, int], porta_peer: int) -> str:
    """
    Busca peers que possuem o arquivo solicitado.
    :param requisicao: A requisição de busca do peer.
    :param endereco_peer: O endereço do peer.
    :param porta_peer: A porta de servidor do peer.
    :return: A mensagem de resposta.
    """
    nome_arquivo = requisicao.get('nome_arquivo')

    with mutex_peers:
        resultado = [
            {'id_peer': id_peer, 'endereco': peer['endereco']}
            for id_peer, peer in peers.items()
            if nome_arquivo in peer['arquivos']
        ]

    return json.dumps(
        {'status': 'sucesso', 'peers': resultado} if resultado else
        {'status': 'erro', 'mensagem': 'Arquivo não encontrado.'}
    )


def lidar_com_lista(requisicao: dict[str, any], endereco_peer: tuple[str, int], porta_peer: int) -> str:
    """
    Retorna a lista de todos os peers e seus arquivos.
    :param requisicao: A requisição de lista do peer.
    :param endereco_peer: O endereço do peer.
    :param porta_peer: A porta de servidor do peer.
    :return: A mensagem de resposta.
    """
    with mutex_peers:
        lista_peers = {
            id_peer: {
                'arquivos': peer['arquivos'],
                'endereco': peer['endereco'],
                'score': peer['score']
            }
            for id_peer, peer in peers.items()
        }

    return json.dumps({'status': 'sucesso', 'peers': lista_peers})


def remover_peers_inativos() -> None:
    """
    Remove peers inativos da lista global.
    :return: None
    """
    while True:
        with mutex_peers:
            tempo_atual = time.time()
            peers_inativos = [
                id_peer
                for id_peer, peer in peers.items()
                if tempo_atual - peer['ultima_atividade'] > 60
            ]
            for id_peer in peers_inativos:
                peers.pop(id_peer)
                print(f'Peer {id_peer} removido por inatividade.')

        time.sleep(30)


if __name__ == '__main__':
    iniciar_tracker(HOST_TRACKER, PORTA_TRACKER)
