# CamadaEnlace/correcao_erros.py

class CorrecaoErros:
    """
    Implementa protocolos para correção de erros na camada de enlace.
    Atualmente suporta o Código de Hamming para detecção e correção de erros de bit único.
    """

    def __init__(self):
        """
        Inicializa a classe CorrecaoErros.
        Não requer parâmetros de inicialização específicos para os métodos atuais.
        """
        pass

    def _determine_parity_bits(self, data_len: int) -> int:
        """
        Determina o número necessário de bits de paridade (m) para um dado comprimento de bits de dados (n).
        A relação é dada por 2^m >= n + m + 1.

        Args:
            data_len (int): O número de bits de dados (n).

        Returns:
            int: O número de bits de paridade (m) necessários.
        """
        m = 0
        while (2**m) < (data_len + m + 1):
            m += 1
        return m

    def _is_power_of_two(self, n: int) -> bool:
        """
        Verifica se um número é uma potência de dois.
        (Ex: 1, 2, 4, 8, ...).
        Isso é usado para identificar as posições dos bits de paridade no codeword de Hamming.

        Args:
            n (int): O número a ser verificado.

        Returns:
            bool: True se for uma potência de dois, False caso contrário.
        """
        return n > 0 and (n & (n - 1)) == 0

    def adicionar_hamming(self, data_bits_str: str) -> str:
        """
        Aplica o Código de Hamming para detecção e correção de um único erro.
        Esta função pega uma sequência de bits de dados e adiciona os bits de paridade
        necessários para formar um 'codeword' de Hamming.

        Args:
            data_bits_str (str): Uma string contendo '0's e '1's representando os bits de dados originais.

        Returns:
            str: O codeword de Hamming resultante (bits de dados + bits de paridade).
        """
        # Converte a string de bits para uma lista de inteiros (0 ou 1) para facilitar a manipulação.
        data_bits = [int(b) for b in data_bits_str]
        n = len(data_bits)  # Número de bits de dados

        # 1. Determina o número de bits de paridade (m) necessários.
        m = self._determine_parity_bits(n)
        total_len = n + m  # Comprimento total do codeword Hamming

        # Inicializa o codeword com zeros.
        # As posições dos bits de paridade (potências de 2: 1, 2, 4, 8...)
        # serão preenchidas posteriormente.
        codeword = [0] * total_len

        # 2. Insere os bits de dados nas posições que NÃO são de paridade.
        # Percorre o codeword. Se a posição (1-indexada) não for potência de 2,
        # é uma posição para um bit de dado.
        data_idx = 0
        for i in range(total_len):
            # As posições de paridade são 1, 2, 4, 8... (1-indexado).
            # Em 0-indexado, são 0, 1, 3, 7...
            if not self._is_power_of_two(i + 1): # Se (i+1) NÃO for potência de 2
                if data_idx < n:
                    codeword[i] = data_bits[data_idx]
                    data_idx += 1
                else:
                    # Isso não deve acontecer se a lógica estiver correta, mas é um safeguard.
                    # print("Aviso: Mais posições de dados do que bits de dados disponíveis.")
                    pass

        # 3. Calcula e preenche os bits de paridade.
        # Para cada bit de paridade (p_i em posições 2^0, 2^1, 2^2, ...):
        # p_i cobre todos os bits (dados e paridade) cujo bit (i-ésimo) em sua representação binária é 1.
        for i in range(m):
            parity_pos_1_indexed = (2**i) # Posição 1, 2, 4, 8... (1-indexado)
            
            count_ones = 0
            # Itera por todas as posições do codeword (0-indexado)
            for j in range(total_len):
                # Se o bit na posição (j+1) (1-indexada) tem o i-ésimo bit (referente a parity_pos_1_indexed)
                # de sua representação binária definido como 1, ele contribui para a paridade.
                # E se o bit atual em codeword[j] for '1'.
                if ((j + 1) & parity_pos_1_indexed) != 0: # Verifica se o bit contribui para esta paridade
                    if codeword[j] == 1:
                        count_ones += 1
            
            # Se a contagem de '1's for ímpar, o bit de paridade deve ser '1' para tornar a paridade par.
            if count_ones % 2 != 0:
                codeword[parity_pos_1_indexed - 1] = 1 # A posição do bit de paridade no codeword (0-indexado)

        # Converte a lista de inteiros de volta para string de bits.
        return "".join(map(str, codeword))

    def corrigir_hamming(self, codeword_str: str) -> tuple[str, str | None]:
        """
        Corrige um erro de bit único em um codeword Hamming recebido.
        Calcula a síndrome para identificar a posição do erro. Se a síndrome for zero, não há erro.
        Se for diferente de zero, indica a posição (1-indexada) do bit com erro, que é então invertido.
        Detecta múltiplos erros (síndrome > total_len ou 0), mas só corrige um.

        Args:
            codeword_str (str): A string do codeword Hamming recebido, potencialmente com um erro.

        Returns:
            tuple[str, str | None]: Uma tupla contendo o codeword corrigido e uma mensagem de status.
                                    A mensagem é None se não houver erro ou o erro for corrigido.
                                    Contém uma string de aviso se o erro não puder ser corrigido (multi-bit).
        """
        codeword = [int(b) for b in codeword_str]
        total_len = len(codeword) # Comprimento total do codeword

        # 1. Determina o número de bits de paridade (m) baseado no comprimento total.
        m = 0
        while (2**m) < (total_len + 1):
            m += 1

        syndrome = 0 # Inicializa a síndrome (que indicará a posição do erro, se houver)

        # 2. Calcula a síndrome.
        # Cada bit de paridade (p_i) é recalculado. Se o recalculado não corresponder ao recebido,
        # o bit correspondente da síndrome é definido.
        for i in range(m):
            parity_pos_1_indexed = (2**i) # Posição 1, 2, 4, 8... (1-indexado)

            count_ones = 0
            # Itera por todas as posições do codeword (0-indexado)
            for j in range(total_len):
                # Verifica se o bit na posição (j+1) (1-indexada) contribui para o bit de paridade 'parity_pos_1_indexed'.
                # E se o bit atual em codeword[j] for '1'.
                if ((j + 1) & parity_pos_1_indexed) != 0:
                    if codeword[j] == 1:
                        count_ones += 1
            
            # Se a paridade recalculada for ímpar (count_ones % 2 != 0),
            # significa que há um erro em algum bit que contribui para esta paridade.
            # Adiciona o valor da posição da paridade à síndrome.
            if count_ones % 2 != 0:
                syndrome |= parity_pos_1_indexed # A síndrome é a soma XOR das posições de paridade falhas

        # 3. Corrige o erro, se detectado.
        if syndrome > 0:
            # Se a síndrome for diferente de zero, ela indica a posição (1-indexada) do bit com erro.
            error_pos_0_indexed = syndrome - 1 # Converte para 0-indexado
            
            if error_pos_0_indexed < total_len:
                # Inverte o bit na posição do erro.
                codeword[error_pos_0_indexed] = 1 - codeword[error_pos_0_indexed] # Inverte 0 para 1, ou 1 para 0
                corrected_codeword_str = "".join(map(str, codeword))
                
                # Mensagem de log/status
                message = f"Erro detectado na posição {syndrome} (1-indexado) e corrigido." \
                          f" Bit original era '{codeword_str[error_pos_0_indexed]}' agora é '{corrected_codeword_str[error_pos_0_indexed]}'."
                return corrected_codeword_str, message
            else:
                # Síndrome indica uma posição fora do codeword, o que geralmente significa múltiplos erros.
                message = f"Erro multi-bit detectado ou posição de erro inválida (síndrome {syndrome}). Não é possível corrigir com Hamming de bit único."
                return codeword_str, message # Retorna o codeword original se não puder corrigir
        else:
            # Síndrome zero significa que nenhum erro foi detectado.
            return codeword_str, "Nenhum erro detectado."

    def remover_redundancia_hamming(self, codeword_str: str) -> str:
        """
        Remove os bits de paridade de um codeword Hamming (assumindo que já foi corrigido, se necessário)
        para obter os bits de dados originais.

        Args:
            codeword_str (str): A string do codeword Hamming (corrigido).

        Returns:
            str: A string dos bits de dados originais, sem os bits de paridade.
        """
        codeword = [int(b) for b in codeword_str]
        original_data_bits = []
        total_len = len(codeword)

        # Percorre o codeword e coleta apenas os bits que NÃO são de paridade.
        for i in range(total_len):
            # Se a posição (1-indexada) NÃO for uma potência de dois, é um bit de dado.
            if not self._is_power_of_two(i + 1):
                original_data_bits.append(codeword[i])
                
        return "".join(map(str, original_data_bits))


# --- Funções e Mapeamentos para a opção 'Nenhuma' ---
# Embora a classe seja preferível, manter estas funções de wrapper
# e o dicionário permite a integração flexível com a GUI.

def nenhuma_correcao_tx(data_bits: str) -> str:
    """
    Função placeholder para o cenário onde nenhuma correção de erros é aplicada no transmissor (Tx).
    Simplesmente retorna os bits de dados como estão, sem adicionar qualquer redundância de correção.

    Args:
        data_bits (str): A string de bits de dados a ser transmitida.

    Returns:
        str: A mesma string de bits de dados, sem modificação.
    """
    return data_bits

def nenhuma_correcao_rx(codeword: str) -> tuple[str, str]:
    """
    Função placeholder para o cenário onde nenhuma correção de erros é aplicada no receptor (Rx).
    Simplesmente retorna o codeword recebido como está e uma mensagem indicando que nenhuma
    correção foi realizada.

    Args:
        codeword (str): A string do codeword recebido.

    Returns:
        tuple[str, str]: Uma tupla contendo o codeword recebido e uma mensagem de status.
    """
    return codeword, "Correção de Erros: Nenhuma."

def nenhuma_remocao_redundancia(codeword: str) -> str:
    """
    Função placeholder para o cenário onde não há redundância a ser removida (após a recepção).
    Isto é usado quando 'Nenhuma' correção de erros é selecionada.

    Args:
        codeword (str): A string do codeword recebido.

    Returns:
        str: A mesma string do codeword, sem modificação.
    """
    return codeword


# Mapeamento de protocolos para uso no simulador (facilita a seleção via GUI)
# Cada chave corresponde a uma opção de protocolo na GUI, e o valor é a função a ser chamada.

CORRECAO_ERROS_TX = {
    'Hamming': CorrecaoErros().adicionar_hamming,
    'Nenhuma': nenhuma_correcao_tx
}

CORRECAO_ERROS_RX = {
    'Hamming': CorrecaoErros().corrigir_hamming,
    'Nenhuma': nenhuma_correcao_rx
}

# Novo mapeamento para a remoção final de redundância para a camada de aplicação
REMOVER_RED_CORRECAO_ERROS_RX = {
    'Hamming': CorrecaoErros().remover_redundancia_hamming,
    'Nenhuma': nenhuma_remocao_redundancia
}