# CamadaEnlace/correcao_erros.py

def _get_parity_positions(data_len: int) -> list[int]:
    """Calcula as posições dos bits de paridade para o Código de Hamming."""
    parity_positions = []
    k = 0
    while (2**k) - 1 < (data_len + k): # 2^k - 1 deve ser menor que o comprimento total (data + paridade)
        parity_positions.append(2**k - 1) # Posições 0-indexadas (1, 2, 4, 8...)
        k += 1
    return parity_positions

def adicionar_hamming(data_bits: str) -> str:
    """
    Aplica o Código de Hamming para detecção e correção de um único erro.
    Retorna o codeword Hamming.
    """
    # 1. Determinar o número de bits de paridade (m)
    # 2^m >= n + m + 1, onde n é o número de bits de dados
    n = len(data_bits)
    m = 0
    while (2**m) < (n + m + 1):
        m += 1

    total_len = n + m
    codeword = ['0'] * total_len # Inicializa com zeros

    # 2. Inserir bits de dados nas posições não-paridade
    data_idx = 0
    for i in range(total_len):
        # Posições de potência de 2 são bits de paridade (1, 2, 4, 8...)
        # Um número é potência de 2 se (num & (num - 1)) == 0
        # No nosso caso, queremos 1, 2, 4, ... então (i+1)
        if ((i + 1) & i) == 0: # (i+1) é potência de 2 (0-indexado)
            # Esta é uma posição de paridade, deixa como '0' por enquanto
            continue
        else:
            codeword[i] = data_bits[data_idx]
            data_idx += 1

    # 3. Calcular bits de paridade
    for i in range(m):
        parity_pos = (2**i) - 1 # Posição 0-indexada do bit de paridade
        count = 0
        for j in range(total_len):
            if ((j + 1) & (parity_pos + 1)) != 0 and codeword[j] == '1':
                count += 1
        
        if count % 2 != 0: # Paridade ímpar, então o bit de paridade deve ser '1'
            codeword[parity_pos] = '1'
        # else: bit já é '0'

    return "".join(codeword)

def corrigir_hamming(codeword: str) -> str:
    """
    Corrige um erro no codeword Hamming e retorna o codeword corrigido.
    Detecta múltiplos erros, mas só corrige um.
    """
    # 1. Determinar o número de bits de paridade (m)
    total_len = len(codeword)
    m = 0
    while (2**m) < (total_len + 1):
        m += 1

    syndrome = 0
    # 2. Calcular bits de paridade e formar síndromes
    for i in range(m):
        parity_pos = (2**i) # Posição 1-indexada para cálculo da síndrome
        count = 0
        for j in range(total_len): # Percorre todas as posições 0-indexadas
            # Verifica se o bit na posição (j+1) contribui para o bit de paridade 'parity_pos'
            if ((j + 1) & parity_pos) != 0 and codeword[j] == '1':
                count += 1
        
        if count % 2 != 0: # Se a paridade for ímpar, há um erro no grupo
            syndrome |= parity_pos # Adiciona ao valor da síndrome

    # 3. Corrigir o erro
    if syndrome > 0:
        # A posição do bit com erro é (syndrome - 1)
        error_pos_0_indexed = syndrome - 1
        if error_pos_0_indexed < total_len:
            codeword_list = list(codeword)
            # Inverte o bit na posição do erro
            codeword_list[error_pos_0_indexed] = '1' if codeword_list[error_pos_0_indexed] == '0' else '0'
            corrected_codeword = "".join(codeword_list)
            print(f"  Hamming: Erro detectado na posição {syndrome} (1-indexado) e corrigido. Bit original era '{codeword[error_pos_0_indexed]}' agora é '{corrected_codeword[error_pos_0_indexed]}'.")
            return corrected_codeword
        else:
            print(f"  Hamming: Erro multi-bit detectado ou posição de erro fora dos limites (síndrome {syndrome}). Não é possível corrigir.")
            return codeword # Retorna o codeword original se não puder corrigir
    else:
        print("  Hamming: Nenhum erro detectado.")
        return codeword

def remover_redundancia_hamming(codeword: str) -> str:
    """
    Remove os bits de paridade de um codeword Hamming corrigido
    para obter os bits de dados originais.
    """
    original_data_bits = []
    total_len = len(codeword)
    for i in range(total_len):
        # Posições de potência de 2 (1, 2, 4, 8...) são bits de paridade
        if ((i + 1) & i) == 0: # (i+1) é potência de 2 (0-indexado)
            continue
        else:
            original_data_bits.append(codeword[i])
    return "".join(original_data_bits)


# --- Funções para a opção 'Nenhuma' ---
def nenhuma_correcao_tx(data_bits: str) -> str:
    """Função placeholder para 'Nenhuma' correção de erros no Tx."""
    return data_bits

def nenhuma_correcao_rx(codeword: str) -> str:
    """Função placeholder para 'Nenhuma' correção de erros no Rx."""
    print("  Correção de Erros: Nenhuma.")
    return codeword

def nenhuma_remocao_redundancia(codeword: str) -> str:
    """Função placeholder para 'Nenhuma' remoção de redundância."""
    return codeword


# Mapeamento para uso no simulador
CORRECAO_ERROS_TX = {
    'Hamming': adicionar_hamming,
    'Nenhuma': nenhuma_correcao_tx
}

CORRECAO_ERROS_RX = {
    'Hamming': corrigir_hamming,
    'Nenhuma': nenhuma_correcao_rx
}

# Novo mapeamento para a remoção final de redundância para a camada de aplicação
REMOVER_RED_CORRECAO_ERROS_RX = {
    'Hamming': remover_redundancia_hamming,
    'Nenhuma': nenhuma_remocao_redundancia
}