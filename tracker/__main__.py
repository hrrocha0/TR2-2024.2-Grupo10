import sys

from socket import *
from threading import *
from message import *

HOST = '127.0.0.1'
PORT = 8000

__users: dict[str, str] = {}


def main() -> None:
    """
    Teleinformática e Redes (2024.2) - Grupo 10

    - Henrique Rodrigues Rocha - 211036061
    -
    -
    :return: None
    """
    try:
        server_socket = create_socket(HOST, PORT)

        print(f'Ouvindo em {HOST}:{PORT}...')

        while True:
            client_socket, client_address = server_socket.accept()

            client_thread = Thread(target=handle_peer, args=(client_socket, client_address))
            client_thread.start()
    except IOError as e:
        print(f'Erro: {e}')
        sys.exit(1)


def create_socket(host: str, port: int) -> socket:
    """
    Cria um socket TCP de servidor com o endereço e porta especificados.
    :param host: O endereço IP ou DNS do servidor.
    :param port: A porta do servidor.
    :return: O socket criado.
    """
    server_socket = socket(AF_INET, SOCK_STREAM)
    server_socket.bind((host, port))
    server_socket.listen(1)

    return server_socket


def handle_peer(client_socket: socket, client_address: (str, int)) -> None:
    """
    Responde às requisições de um peer.
    :param client_socket: O socket do peer.
    :param client_address: O endereço IP e porta do peer.
    :return: None
    """
    while True:
        encoded = client_socket.recv(1024)
        request = Message.from_utf8(encoded)

        match request.message_type:
            case _:
                pass


if __name__ == '__main__':
    main()
