from socket import *


def criar_socket_servidor(host: str, porta: int) -> socket:
    """
    Cria um socket TCP de servidor.
    :param host: O host do servidor.
    :param porta: A porta do servidor.
    :return: O socket TCP criado.
    """
    socket_servidor = socket(AF_INET, SOCK_STREAM)
    socket_servidor.bind((host, porta))
    socket_servidor.listen(5)

    return socket_servidor


def criar_socket_cliente(host: str, porta: int) -> socket:
    socket_cliente = socket(AF_INET, SOCK_STREAM)
    socket_cliente.connect((host, porta))

    return socket_cliente
