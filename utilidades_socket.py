from socket import *


def criar_servidor_socket(host: str, porta: int) -> socket:
    """
    Cria um socket TCP de servidor.
    :param host: O host do servidor.
    :param porta: A porta do servidor.
    :return: O socket TCP criado.
    """
    servidor_socket = socket(AF_INET, SOCK_STREAM)
    servidor_socket.bind((host, porta))
    servidor_socket.listen(5)

    return servidor_socket


def criar_cliente_socket(host: str, porta: int) -> socket:
    cliente_socket = socket(AF_INET, SOCK_STREAM)
    cliente_socket.connect((host, porta))

    return cliente_socket
