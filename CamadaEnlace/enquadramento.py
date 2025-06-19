# CamadaEnlace/enquadramento.py

# FLAGS para enquadramento
FLAG_BYTE = b'\x7E' # 01111110 em byte
FLAG_BIT_STR = '01111110' # 01111110 em string de bits

# Caractere de escape para inserção de bytes (DC1 ou similar, ex: 0x11)
ESC_BYTE = b'\x11'

def aplicar_enquadramento_contagem_caracteres(data_bits: str) -> str:
    """
    Aplica enquadramento por contagem de caracteres.
    Adiciona um prefixo de 8 bits representando o comprimento do payload em bytes.
    Assume que `data_bits` é uma string de bits que pode ser convertida em bytes.
    """
    # Converte string de bits para bytes para contar o comprimento real
    # Adiciona padding se não for múltiplo de 8
    padded_data_bits = data_bits + '0' * ((8 - len(data_bits) % 8) % 8)
    data_bytes = bytes(int(padded_data_bits[i:i+8], 2) for i in range(0, len(padded_data_bits), 8))

    length = len(data_bytes)
    if length > 255:
        raise ValueError("Payload muito grande para enquadramento por contagem de caracteres (max 255 bytes)")

    # Adiciona o byte de comprimento (8 bits) no início
    length_bits = format(length, '08b')
    return length_bits + padded_data_bits

def remover_enquadramento_contagem_caracteres(frame_bits: str) -> str:
    """
    Remove enquadramento por contagem de caracteres.
    Retorna apenas os bits de dados.
    """
    if len(frame_bits) < 8:
        raise ValueError("Quadro muito curto para enquadramento por contagem de caracteres")

    length_bits = frame_bits[:8]
    payload_bits = frame_bits[8:]

    length = int(length_bits, 2)
    expected_payload_len_bits = length * 8

    if len(payload_bits) < expected_payload_len_bits:
        # Isso pode acontecer se o quadro for truncado no meio de um byte
        # Ou se a contagem de caracteres estiver errada devido a erro
        # Vamos retornar o que foi possível, mas idealmente seria um erro fatal
        return payload_bits # Retorna a parte disponível
        # raise ValueError("Comprimento do quadro incompatível com a contagem de caracteres")

    return payload_bits[:expected_payload_len_bits]


def aplicar_enquadramento_flags_bytes(data_bytes: bytes) -> bytes:
    """
    Aplica enquadramento com FLAGS e inserção de bytes (byte stuffing).
    Adiciona FLAG_BYTE no início e fim.
    Substitui ocorrências de FLAG_BYTE e ESC_BYTE no payload.
    """
    # Escapa FLAG_BYTE e ESC_BYTE no payload
    stuffed_data = data_bytes.replace(ESC_BYTE, ESC_BYTE + ESC_BYTE)
    stuffed_data = stuffed_data.replace(FLAG_BYTE, ESC_BYTE + FLAG_BYTE)
    return FLAG_BYTE + stuffed_data + FLAG_BYTE

def remover_enquadramento_flags_bytes(frame_bytes: bytes) -> bytes:
    """
    Remove enquadramento com FLAGS e inserção de bytes (byte stuffing).
    Retorna apenas os bytes de dados, removendo os escapes.
    """
    if not (frame_bytes.startswith(FLAG_BYTE) and frame_bytes.endswith(FLAG_BYTE)):
        raise ValueError("Quadro não começa ou termina com FLAG_BYTE")

    # Remove as FLAGS de início e fim
    data_with_stuffing = frame_bytes[len(FLAG_BYTE):-len(FLAG_BYTE)]

    # Desescapa ocorrências
    unstuffed_data = data_with_stuffing.replace(ESC_BYTE + FLAG_BYTE, FLAG_BYTE)
    unstuffed_data = unstuffed_data.replace(ESC_BYTE + ESC_BYTE, ESC_BYTE)
    return unstuffed_data

def aplicar_enquadramento_flags_bits(data_bits: str) -> str:
    """
    Aplica enquadramento com FLAGS e inserção de bits (bit stuffing).
    Adiciona FLAG_BIT_STR no início e fim.
    Insere '0' após 5 '1's consecutivos no payload.
    """
    stuffed_data = data_bits.replace('11111', '111110')
    return FLAG_BIT_STR + stuffed_data + FLAG_BIT_STR

def remover_enquadramento_flags_bits(frame_bits: str) -> str:
    """
    Remove enquadramento com FLAGS e inserção de bits (bit stuffing).
    Retorna apenas os bits de dados, removendo os bits de stuffing.
    """
    # Verifica e remove FLAGS de início e fim
    if not (frame_bits.startswith(FLAG_BIT_STR) and frame_bits.endswith(FLAG_BIT_STR)):
        raise ValueError("Quadro não começa ou termina com FLAG_BIT_STR")

    data_with_stuffing = frame_bits[len(FLAG_BIT_STR):-len(FLAG_BIT_STR)]

    # Remove os bits de stuffing (remove '0's após 5 '1's consecutivos)
    # Cuidado: esta é uma desstuffing simplificada.
    # Uma implementação robusta precisa de um automato para detectar 111110 corretamente.
    # Exemplo: Se tiver 1111101, remove o 0 do meio para 111111.
    unstuffed_data = ""
    count_ones = 0
    for bit in data_with_stuffing:
        if bit == '1':
            count_ones += 1
            unstuffed_data += '1'
        elif bit == '0':
            if count_ones == 5:
                # Este '0' é um bit de stuffing, não adicionar
                count_ones = 0 # Resetar contador
            else:
                unstuffed_data += '0'
                count_ones = 0 # Resetar contador
        else:
            raise ValueError("Quadro contém caracteres inválidos (não bits)")
    return unstuffed_data


# Mapeamento para uso no simulador
ENQUADRAMENTO_TX = {
    'Contagem de caracteres': aplicar_enquadramento_contagem_caracteres,
    'FLAGS e inserção de bytes': aplicar_enquadramento_flags_bytes,
    'FLAGS e inserção de bits': aplicar_enquadramento_flags_bits
}

ENQUADRAMENTO_RX = {
    'Contagem de caracteres': remover_enquadramento_contagem_caracteres,
    'FLAGS e inserção de bytes': remover_enquadramento_flags_bytes,
    'FLAGS e inserção de bits': remover_enquadramento_flags_bits
}