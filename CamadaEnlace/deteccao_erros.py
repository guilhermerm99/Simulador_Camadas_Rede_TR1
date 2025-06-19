# CamadaEnlace/deteccao_erros.py

def calcular_paridade_par(data_bits: str) -> str:
    """
    Calcula o bit de paridade par para uma string de bits.
    A paridade par significa que o número total de '1's (incluindo o bit de paridade) é par.
    """
    count_ones = data_bits.count('1')
    parity_bit = '1' if count_ones % 2 != 0 else '0' # Se a contagem for ímpar, adicione 1 para tornar par
    return parity_bit

def adicionar_paridade_par(data_bits: str) -> str:
    """Adiciona um bit de paridade par ao final dos dados."""
    parity_bit = calcular_paridade_par(data_bits)
    return data_bits + parity_bit

def verificar_paridade_par(frame_bits: str) -> bool:
    """
    Verifica se o quadro (data + paridade) tem paridade par.
    Retorna True se nenhum erro for detectado, False se erro for detectado.
    """
    if not frame_bits:
        return True # Ou levante um erro, dependendo da especificação para dados vazios

    # O último bit é o bit de paridade
    data_and_parity = frame_bits
    count_ones = data_and_parity.count('1')
    return count_ones % 2 == 0 # Se a contagem total de 1s for par, não há erro detectado


# --- CRC-32 (IEEE 802.3) ---
# Polinômio para CRC-32 (IEEE 802.3)
# Representação em binário: 100000100110000010001110110110111 (33 bits)
# Em hexadecimal (ignora o bit mais significativo): 0x04C11DB7
# O bit mais significativo é implícito no CRC.
POLINOMIO_CRC32_IEEE = 0x04C11DB7 # 00000100110000011101101101111 (IEEE 802.3, ethernet)
GRAU_CRC32 = 32

def _xor_bits(a: str, b: str) -> str:
    """Realiza XOR bit a bit em strings de bits de mesmo comprimento."""
    return ''.join(['1' if bit_a != bit_b else '0' for bit_a, bit_b in zip(a, b)])

def calcular_crc(data_bits: str, polynomial: int, degree: int) -> str:
    """
    Calcula o Cyclic Redundancy Check (CRC) para uma string de bits.
    Implementação simplificada de divisão binária.
    """
    # Adiciona 'degree' zeros ao final dos dados para a divisão
    augmented_data = data_bits + '0' * degree
    
    # Converte o polinômio para string de bits para fácil manipulação
    # Adiciona '1' no MSB implícito para o divisor binário
    divisor_bits = format(polynomial, f'0{degree}b')
    divisor_bits = '1' + divisor_bits # Inclui o 1 implícito

    # Convertendo para lista de caracteres para manipulação mutável
    data_list = list(augmented_data)
    len_divisor = len(divisor_bits)
    len_data = len(data_list)

    # Processo de divisão binária
    for i in range(len_data - len_divisor + 1):
        if data_list[i] == '1': # Se o bit atual é '1', realiza XOR
            for j in range(len_divisor):
                data_list[i+j] = '1' if data_list[i+j] != divisor_bits[j] else '0'
    
    # O resto da divisão são os bits CRC
    remainder = "".join(data_list[len_data - degree:])
    return remainder

def adicionar_crc32(data_bits: str) -> str:
    """Adiciona o CRC-32 aos bits de dados."""
    crc = calcular_crc(data_bits, POLINOMIO_CRC32_IEEE, GRAU_CRC32)
    return data_bits + crc

def verificar_crc32(frame_bits: str) -> bool:
    """
    Verifica o CRC-32 de um quadro (data + CRC).
    Retorna True se nenhum erro for detectado (resto zero), False caso contrário.
    """
    if len(frame_bits) < GRAU_CRC32:
        return False # Quadro muito curto para ter CRC

    # Se o resto da divisão do quadro completo for zero, então não há erro
    remainder = calcular_crc(frame_bits, POLINOMIO_CRC32_IEEE, GRAU_CRC32)
    return int(remainder, 2) == 0 # Retorna True se o resto for zero


# --- Funções para a opção 'Nenhuma' na detecção de erros ---
def nenhuma_deteccao_tx(data_bits: str) -> str:
    """Função placeholder para 'Nenhuma' detecção de erros no Tx."""
    return data_bits

def nenhuma_deteccao_rx(frame_bits: str) -> bool:
    """Função placeholder para 'Nenhuma' detecção de erros no Rx. Sempre retorna True (sem erro)."""
    print("  Detecção de Erros: Nenhuma. Presumindo ausência de erro.")
    return True # Assume que não há erro detectado se não há mecanismo


# Mapeamento para uso no simulador
DETECCAO_ERROS_TX = {
    'Bit de paridade par': adicionar_paridade_par,
    'CRC-32': adicionar_crc32,
    'Nenhuma': nenhuma_deteccao_tx # Adiciona a opção 'Nenhuma'
}

DETECCAO_ERROS_RX = {
    'Bit de paridade par': verificar_paridade_par,
    'CRC-32': verificar_crc32,
    'Nenhuma': nenhuma_deteccao_rx # Adiciona a opção 'Nenhuma'
}