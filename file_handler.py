import os
import math
import hashlib


def count_blocks(file_size: int, peer_num: int,
                 block_size: int = 100000000) -> list:
    """
    Determina quantos e quais blocos do arquivo cada peer deve criar para um
    dado tamanho de bloco.

    Args:
        file_name (str): O nome do arquivo.
        file_size (int): Tamanho (bytes) do arquivo.
        peer_num (int): Quantidade de peers envolvidos.
        block_size (int): Quantidade de bytes por bloco (padrão = 100Mb).
        folder (str): O diretório no qual o arquivo se encontra.

    Returns:
        list: Uma lista de duplas que informam a partir de qual bloco cada peer
        deve começar a criar blocos e quantos eles devem criar.
    """
    # Determina a quantidade de blocos a serem criados.
    block_num = math.ceil(file_size / block_size)

    # Determina quantos blocos cada peer deve criar.
    blocks_per_peer = block_num // peer_num
    remainder = block_num % peer_num

    # Espalhar a quantidade de blocos entre os peers.
    pre_assignments = [blocks_per_peer] * peer_num

    for i in range(remainder):
        pre_assignments[i] += 1

    # Criar a lista de duplas para retorno.
    position = 0
    assignments = []
    for i in pre_assignments:
        assignments.append((position, i))
        position += i

    return assignments


def create_blocks(file_name: str, start: int, block_num: int,
                  block_size: int = 100000000, folder: str = "files/") -> list:
    """
    Cria um número específico de blocos do arquivo, a partir de um ponto
    específico.

    Args:
        file_name (str): O nome do arquivo.
        start (int): O bloco do arquivo no qual se começa.
        block_num (int): Quantidade de blocos a serem criados.
        block_size (int): Tamanho (bytes) de cada bloco (padrão = 100Mb).
        folder (str): O diretório no qual o arquivo se encontra.

    Returns:
        list: Lista de nomes dos blocos do arquivo.
    """
    # Pega o nº do bloco inicial.
    i = start

    # Lista de nomes/diretórios dos blocos.
    block_names = []

    with open(folder + file_name, "rb") as file:

        # Percorre o arquivo até o primeiro pedaço que será lido.
        file.seek(start * block_size)

        while block_num:

            # Cria um arquivo novo para cada bloco. Adiciona ele a lista.
            block = file_name + "_block" + str(i)
            block_names.append(block)
            with open(folder + block, "wb") as b:

                # Lê o nº de bytes equivalente ao tamanho do bloco.
                data = file.read(block_size)
                # Escreve o conteúdo no bloco.
                b.write(data)

            # Reduz quantidade de blocos que faltam e incrementa o nº do bloco.
            block_num -= 1
            i += 1

    return block_names


def combine_blocks(block_names: list, block_folder: str = "files/") -> str:
    """
    Combina os blocos no arquivo original.

    Args:
        block_names (list): Lista de nomes dos blocos.
        block_folder (str): O diretório no qual os blocos se encontram.

    Returns:
        str: Caminho para o arquivo completo.
    """
    # Pega o nº de bytes por bloco.
    byte_num = os.path.getsize(block_folder + block_names[0])
    
    # Cria o arquivo no qual se irá concatenar os bytes dos blocos.
    file_path = block_folder + block_names[0].split("_block")[0]
    #file = path
    with open(file_path, "wb") as f:
        
        # Percorre a lista de nomes/diretórios, concatenando o conteúdo deles.
        for block in block_names:
            
            with open(block_folder + block, "rb") as b:
                
                data = b.read(byte_num)
                f.write(data)

            # Apaga o bloco após operação. Comente se quiser ver os blocos.
            os.remove(block_folder + block)

    return file_path


def calculate_checksum(file_name: str, folder: str = "files/") -> bytes:
    """
    Lê o arquivo/bloco e realiza o checksum/hash de seus bits.

    Args:
        file_name (str): O nome do arquivo.
        folder (str): O diretório no qual o arquivo se encontra.

    Returns:
        bytes: Checksum/hash SHA256 (32 bytes) do arquivo/bloco.
    """
    # Abre o arquivo e lê os dados.
    with open(folder + file_name, "rb") as f:
        data = f.read()
    
    # Calcula o hash.
    checksum = hashlib.sha256(data)

    # Transforma em bytes.
    result = checksum.digest()

    return result


def append_checksum(file_name: str, folder: str = "files/") -> None:
    """
    Acrescenta o checksum/hash ao final do arquivo/bloco passado.

    Args:
        file_name (str): O nome do arquivo/bloco.
        folder (str): O diretório no qual o arquivo se encontra.

    Returns:
        None
    """
    # Calculando o checksum/hash.
    checksum = calculate_checksum(file_name)

    # Acrescentando ele ao final do arquivo.
    with open(folder + file_name, "ab") as f:
        f.write(checksum)


def extract_checksum(file_name: str, folder: str = "files/") -> bytes:
    """
    Remove e retorna o checksum/hash adicionado ao fim do arquivo/bloco.

    Args:
        file_name (str): O nome do arquivo/bloco.
        folder (str): O diretório no qual o arquivo se encontra.

    Returns:
        bytes: Checksum/hash SHA256 removido do arquivo/bloco.
    """
    # Adquire o tamanho do arquivo sem o checksum.
    file_size = os.path.getsize(folder + file_name) - 32

    # Abre o arquivo, vai os últimos 32 bytes e lê o checksum/hash.
    with open(folder + file_name, "rb+") as f:
        f.seek(-32, 2)
        checksum = f.read()
        # Remove os últimos 32 bytes do arquivo.
        f.truncate(file_size)

    return checksum


def test1():
    """
    Teste de "count_blocks", "create_blocks" e "combine_blocks".
    """
    file_n = input("\nInsira o nome de um arquivo (no subdiretório 'files').\n")
    file_s = os.path.getsize("files/" + file_n)
    print("Tamanho do arquivo (bytes):\n" + str(file_s))
    peer_n = int(input("Insira um número de peers (1 a 4, normalmente).\n"))
    block_s = int(input("E um tamanho de bloco (bytes, e.g. 1.000.000 = 1MB).\n"))
    
    assignments = count_blocks(file_s, peer_n, block_s)

    print("\nLista de atribuições para peers (bloco no qual começa, nº de blocos):")
    print(assignments)

    i = 0
    block_lists = []
    for a in assignments:
        print('"Peer" ' + str(i) + " criando blocos.")
        blocks = create_blocks(file_n, a[0], a[1], block_s)
        block_lists.append(blocks)
        i += 1

    all_blocks = sum(block_lists, [])
    print("\nLista de nomes de blocos criados pelos peers:")
    print(all_blocks)

    print("\nOs blocos estão no mesmo diretório do arquivo.")
    input("Pressione ENTER para continuar. Os blocos serão deletados.\n")

    print("Combinando os blocos.")
    new_file = combine_blocks(all_blocks)
    print("Arquivo criado: " + new_file + "\n\n")


def test2():
    """
    Teste de "calculate_checksum", "append_checksum" e "extract_checksum".
    """
    file_n = input("\nInsira o nome de um arquivo (no subdiretório 'files').\n")

    checksum = calculate_checksum(file_n)

    print("\nChecksum SHA256 do arquivo:")
    print(checksum)
    print("\n")

    print("Acrescentando o checksum no fim do arquivo.")
    append_checksum(file_n)

    print("\nO arquivo deve ter 32 bytes a mais de extensão.")
    input("Pressione ENTER para continuar.\n")

    print("Extraindo o checksum.")
    extracted_checksum = extract_checksum(file_n)
    print("Checksum SHA256 extraído do arquivo:")
    print(extracted_checksum)

    print("Checksums iguais?")
    print(str(checksum == extracted_checksum) + "\n\n")


if __name__ == "__main__":
    while True:
        print("Escolha um teste:\n")
        print('1. Teste de "count_blocks", "create_blocks" e "combine_blocks".')
        print('2. Teste de "calculate_checksum", "append_checksum" e "extract_checksum".')
        print('3. Sair.')

        option = input()

        if option == '1':
            test1()
        elif option == '2':
            test2()
        else:
            break
