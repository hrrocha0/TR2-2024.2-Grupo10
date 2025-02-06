import os
import math


def count_blocks(file_name: str, peer_num: int, block_size: int = 100000000,
                 folder: str = "files/") -> list:
    """
    Determina quantos e quais blocos do arquivo cada peer deve criar para um
    dado tamanho de bloco.

    Args:
        file_name (str): O nome/diretório do arquivo.
        peer_num (int): Quantidade de peers envolvidos.
        block_size (int): Quantidade de bytes por bloco (padrão = 100Mb).
        folder (str): O diretório no qual o arquivo se encontra.

    Returns:
        list: Uma lista de duplas que informam a partir de qual bloco cada peer
        deve começar a criar blocos e quantos eles devem criar.
    """
    # Pega o nº de bytes do arquivo.
    byte_num = os.path.getsize(folder + file_name)

    # Determina a quantidade de blocos a serem criados.
    block_num = math.ceil(byte_num / block_size)

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

    return file_path


def test1():
    """
    Teste de "count_blocks", "create_blocks" e "combine_blocks".
    """
    peer_n = int(input("Insira um número de peers (1 a 4, pela especificação).\n"))
    block_s = int(input("Um tamanho de bloco (bytes, e.g. 1.000.000 = 1MB).\n"))
    file_n = input("E o nome de um arquivo (no subdiretório 'file').\n")
    
    assignments = count_blocks(file_n, peer_n, block_s)

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

    print("\nCombinando os blocos.")
    new_file = combine_blocks(all_blocks)
    print("Arquivo criado: " + new_file)


if __name__ == "__main__":
    test1()
