import json
import sys
import time
from utilidades_socket import *
from threading import *
import os

HOST_TRACKER = '127.0.0.1'
PORTA_TRACKER = 8000

peers = {}
peers_ativos = {}
mutex_peers = Lock()


def iniciar_tracker(host: str, porta: int) -> None:
    """
    Inicia o tracker para o sistema P2P.
    :return: None
    """
    try:
        servidor_socket = criar_servidor_socket(host, porta)
        print(f'Tracker ativo em {host}:{porta}...')

        Thread(target=remover_peers_inativos, daemon=True).start()

        while True:
            cliente_socket, endereco_cliente = servidor_socket.accept()
            print(f'Nova conexão de {endereco_cliente[0]}:{endereco_cliente[1]}.')

            Thread(target=lidar_com_peer, args=(cliente_socket, endereco_cliente)).start()

    except Exception as e:
        print(f'Erro: {e}')
        sys.exit(1)

def handle_request(cliente_socket):
    """
    Processa as requisições do cliente.
    """
    try:
        data = cliente_socket.recv(1024).decode()
        requisicao = json.loads(data)
        tipo = requisicao.get("tipo")
        
        if tipo == "busca":
            nome_arquivo = requisicao.get("nome_arquivo")
            peers_que_tem_arquivo = buscar_arquivo_peers(nome_arquivo)
            
            if peers_que_tem_arquivo:
                resposta = json.dumps(peers_que_tem_arquivo)
            else:
                resposta = json.dumps({"status": "erro", "mensagem": "Nenhum peer encontrado com esse arquivo."})

        elif tipo == "transferencia":
            # Opção para transferência de arquivos
            file_name = requisicao.get('nome_arquivo')
            tamanho_arquivo = os.path.getsize(file_name) if os.path.exists(file_name) else 0
            resposta = json.dumps({"status": "sucesso", "tamanho_arquivo": tamanho_arquivo})
        
        else:
            resposta = json.dumps({"status": "erro", "mensagem": "Tipo de requisição desconhecido."})
        
        cliente_socket.send(resposta.encode('utf-8'))
    except Exception as e:
        print(f"Erro ao processar requisição: {e}")
    finally:
        cliente_socket.close()


def buscar_arquivo_peers(nome_arquivo):
    """
    Busca os peers que possuem o arquivo no tracker.
    """
    peers_que_tem_arquivo = []
    for peers_id, peer_info in peers.items():
        if nome_arquivo in peer_info["arquivos"]:
            peers_que_tem_arquivo.append(peer_info)
    
    return peers_que_tem_arquivo



def criar_servidor_socket(host: str, porta: int) -> socket:
    """
    Cria o socket do servidor para o tracker.
    :param host: Endereço do servidor (ex: '127.0.0.1').
    :param porta: Porta onde o tracker irá escutar.
    :return: Socket configurado para aceitar conexões.
    """
    servidor_socket = socket(AF_INET, SOCK_STREAM)
    servidor_socket.bind((host, porta))
    servidor_socket.listen(5)
    return servidor_socket


def lidar_com_peer(peer_socket, endereco_peer: tuple) -> None:


    """
    Gerencia as comunicações entre tracker e peer.
    :param socket_peer: O socket do peer.
    :param endereco_peer: O endereço do peer.
    :return: None
    """
    try:
        dados = peer_socket.recv(1024).decode('utf-8')
        print(f"Dados recebidos de {endereco_peer}: {dados}")  # Adicionando log

        if not dados:
            print(f"Conexão fechada por {endereco_peer} - Nenhum dado recebido.")
            peer_socket.close()
            return

        requisicao = json.loads(dados)
        print(f"Requisição decodificada: {requisicao}")  # Adicionando log

        porta_peer = requisicao.get('porta', peer_socket.getpeername()[1])
        resposta = processar_requisicao(requisicao, endereco_peer, porta_peer)

        print(f"Resposta: {resposta}")  # Adicionando log
        peer_socket.send(resposta.encode('utf-8'))

    except json.JSONDecodeError as e:
        print(f"Erro ao decodificar JSON: {e}")
    except KeyError as e:
        print(f"Erro de chave ausente: {e}")
    except Exception as e:
        print(f"Erro desconhecido ao lidar com peer {endereco_peer}: {e}")
    finally:
        peer_socket.close()


def processar_requisicao(requisicao: dict, endereco_peer: tuple, porta_peer: int) -> str:
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
        'atualizar_arquivos': lidar_com_atualizar_arquivos,
    }
    tipo = requisicao.get('tipo')

    print(f"Tipo da requisição: {tipo}") 

    if tipo not in operacoes:
        print(f"Tipo de requisição desconhecido: {tipo}") 
        return json.dumps({'status': 'erro', 'mensagem': 'Tipo de mensagem desconhecido.'})

    resposta = operacoes[tipo](requisicao, endereco_peer, porta_peer)
    print(f"Resposta processada: {resposta}")  
    return resposta

def lidar_com_atualizar_arquivos(requisicao: dict, endereco_peer: tuple, porta_peer: int) -> str:
    """
    Atualiza a lista de arquivos de um peer já registrado.
    :param requisicao: A requisição do peer contendo novos arquivos.
    :param endereco_peer: O endereço do peer.
    :param porta_peer: A porta do peer.
    :return: Resposta JSON com status da operação.
    """
    id_peer = requisicao.get('id_peer')
    novos_arquivos = requisicao.get('arquivos', [])

    if not id_peer or not isinstance(novos_arquivos, list):
        return json.dumps({'status': 'erro', 'mensagem': 'ID ou arquivos inválidos.'})

    with mutex_peers:
        if id_peer in peers:
            peers[id_peer]['arquivos'].extend(novos_arquivos)
            peers[id_peer]['arquivos'] = list(set(peers[id_peer]['arquivos']))  
            peers[id_peer]['ultima_atividade'] = time.time()  
            return json.dumps({'status': 'sucesso', 'mensagem': 'Arquivos atualizados com sucesso.'})
        else:
            return json.dumps({'status': 'erro', 'mensagem': 'Peer não encontrado.'})


def lidar_com_busca(requisicao: dict, endereco_peer: tuple, porta_peer: int) -> str:
    nome_arquivo = requisicao.get('nome_arquivo')

    with mutex_peers:
        resultado = [
            {
                'id_peer': id_peer,
                'endereco': peer['endereco'][0], 
                'porta': peer['endereco'][1] 
            }
            for id_peer, peer in peers.items()
            if nome_arquivo in peer['arquivos']
        ]
    
    return json.dumps(
        {'status': 'sucesso', 'peers': resultado} if resultado else
        {'status': 'erro', 'mensagem': 'Arquivo não encontrado.'}
    )


def lidar_com_registro(requisicao: dict, endereco_peer: tuple, porta_peer: int) -> str:
    """
    Registra um peer no tracker.
    :param requisicao: A requisição de registro do peer.
    :param endereco_peer: O endereço do peer.
    :param porta_peer: A porta de servidor do peer.
    :return: A mensagem de resposta.
    """
    id_peer = requisicao.get('id_peer')
    arquivos = requisicao.get('arquivos', [])

    if not id_peer or not isinstance(arquivos, list):
        return json.dumps({'status': 'erro', 'mensagem': 'ID ou arquivos inválidos.'})

    if arquivos is None:
        arquivos = []

    with mutex_peers:
        peers[id_peer] = {
            'endereco': (endereco_peer[0], porta_peer),
            'arquivos': arquivos,
            'ultima_atividade': time.time(),
            'score': 0,
        }
    print(f'Peer {id_peer} registrado com arquivos: {arquivos} e porta: {porta_peer}')

    return json.dumps({'status': 'sucesso', 'mensagem': 'Peer registrado com sucesso.'})




def lidar_com_lista(requisicao: dict, endereco_peer: tuple, porta_peer: int) -> str:
    """
    Retorna a lista de todos os peers e seus arquivos.
    :param requisicao: A requisição de lista do peer.
    :param endereco_peer: O endereço do peer.
    :param porta_peer: A porta de servidor do peer.
    :return: A mensagem de resposta.
    """
    print(f"Solicitação de {endereco_peer} na porta {porta_peer}") 

    with mutex_peers:
        lista_peers = {
            id_peer: {
                'arquivos': peer['arquivos'],
                'endereco': tuple(peer['endereco']),
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
                if tempo_atual - peer['ultima_atividade'] > 120
            ]
            for id_peer in peers_inativos:
                peers.pop(id_peer)
                print(f'Peer {id_peer} removido por inatividade.')

        time.sleep(30)


if __name__ == '__main__':
    iniciar_tracker(HOST_TRACKER, PORTA_TRACKER)
