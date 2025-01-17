from enum import Enum, auto
from typing import Any


class MessageType(Enum):
    pass


class Message:
    """
    Representa uma mensagem da camada de aplicação.
    :var message_type: O tipo da mensagem.
    :var header_parameters: Parâmetros de cabeçalho.
    :var data: Conteúdo da mensagem.
    """
    message_type: MessageType
    header_parameters: dict[str, Any]
    data: bytes

    def __init__(self, message_type: MessageType, header_parameters: dict[str, Any], data: bytes) -> None:
        self.message_type = message_type
        self.header_parameters = header_parameters
        self.data = data

    @classmethod
    def from_utf8(cls, encoded: bytes) -> "Message":
        """
        Converte uma string codificada em UTF-8 em um objeto Message.
        :param encoded: A string codificada.
        :return: O objeto Message correspondente.
        """
        try:
            lines = encoded.decode('utf-8').splitlines()
            message_type = MessageType(lines[0])
            parameters = {}
            data = b''

            counter = 0

            while counter < len(lines):
                if not lines[counter]:
                    break

                parameter, value = lines[counter].split(':')
                parameters[parameter.lower()] = value

                counter += 1

            for line in lines[counter:]:
                data += line

            return cls(message_type, parameters, data)
        except:
            return cls(
                message_type=MessageType.ERROR,
                header_parameters={
                    'code': 'INVALID_MESSAGE',
                    'description': 'A mensagem não corresponde a um comando válido.'
                },
                data=b''
            )

    @classmethod
    def to_utf8(cls, message: "Message") -> bytes:
        """
        Converte um objeto Message em uma string codificada em UTF-8.
        :param message: O objeto Message.
        :return: A string codificada correspondente.
        """
        decoded = f'{message.message_type}\r\n'

        for parameter, value in message.header_parameters.items():
            decoded += f'{parameter.capitalize()}:{value}\r\n'

        if message.data:
            decoded += f'\r\n{message.data}\r\n'

        decoded += '\r\n'

        return decoded.encode('utf-8')
