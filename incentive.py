import os


def incentive_calculation(folder: str = "files/") -> int:
    """
    Determina a quantidade máxima de peers que podem participar de um download.
    Depende da quantidade de arquivos no diretório, bem como do volume total de
    bytes.

    Args:
        folder (str): O diretório no qual o(s) arquivo(s) do peer se encontram.

    Returns:
        int: A quantidade máxima de peers que podem participar de um download.
    """
    peer_num = 1
    byte_total = 0

    # Pega a lista de todos os arquivos no diretório.
    file_list = []
    initial_list = os.listdir(folder)
    for f in initial_list:
        if os.path.isfile(folder + f):
            file_list.append(f)

    # Pega o número de arquivos disponíveis.
    file_num = len(file_list)

    # Somatório do total de bytes sendo "compartilhados".
    for f in file_list:
        byte_total += os.path.getsize(folder + f)

    # Cálculo de incentivo.
    peer_num += (0.1 * file_num)
    peer_num += (0.0000001 * byte_total)

    # Caso a quantidade de peers seja maior do que o limite.
    if peer_num > 4:
        peer_num = 4
        
    return int(peer_num)


if __name__ == "__main__":
    print(incentive_calculation())
