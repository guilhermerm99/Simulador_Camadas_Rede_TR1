# CamadaEnlace/deteccao_erros.py

class DeteccaoErros:
    """
    Implementa protocolos para detecção de erros na camada de enlace.
    Suporta Bit de Paridade Par e CRC-32 (IEEE 802.3).
    """

    # Polinômio gerador CRC-32 (IEEE 802.3)
    # Representação em hexadecimal: 0x04C11DB7.
    # O bit mais significativo (X^32) é implícito e não está incluído nesta representação.
    # Ele é tratado na lógica de divisão.
    CRC32_POLYNOMIAL = 0x04C11DB7
    GRAU_CRC32 = 32

    def __init__(self):
        """Inicializa a classe DeteccaoErros."""
        pass

    # --- Funções de Paridade Par ---
    def calcular_paridade_par(self, data_bits_str: str) -> str:
        """
        Calcula o bit de paridade par para uma sequência de bits.
        A paridade par garante que o número total de '1's (incluindo o bit de paridade) seja um número par.

        Args:
            data_bits_str (str): Uma string contendo '0's e '1's representando os bits de dados.

        Returns:
            str: O bit de paridade ('0' ou '1').
        """
        # Conta o número de bits '1' na sequência de dados.
        count_ones = data_bits_str.count('1')
        
        # Se a contagem for ímpar, o bit de paridade deve ser '1' para tornar a contagem total par.
        # Caso contrário (se a contagem já for par), o bit de paridade deve ser '0'.
        parity_bit = '1' if count_ones % 2 != 0 else '0'
        return parity_bit

    def adicionar_paridade_par(self, data_bits_str: str) -> str:
        """
        Adiciona um bit de paridade par ao final da sequência de bits de dados.

        Args:
            data_bits_str (str): Uma string contendo '0's e '1's representando os bits de dados.

        Returns:
            str: A sequência de bits de dados com o bit de paridade anexado.
        """
        # Calcula o bit de paridade para os dados fornecidos.
        parity_bit = self.calcular_paridade_par(data_bits_str)
        
        # Anexa o bit de paridade ao final dos dados originais.
        return data_bits_str + parity_bit

    def verificar_paridade_par(self, frame_bits_str: str) -> bool:
        """
        Verifica se um quadro (sequência de dados + bit de paridade) tem paridade par.
        Este método é usado no receptor para verificar se houve um erro de bit único.

        Args:
            frame_bits_str (str): Uma string contendo '0's e '1's representando o quadro completo
                                  (dados + bit de paridade).

        Returns:
            bool: True se a contagem total de '1's no quadro for par (nenhum erro detectado).
                  False se a contagem total de '1's for ímpar (erro detectado).
        """
        if not frame_bits_str:
            return True 
        
        # DEBUG: Adiciona este print para verificar a entrada (Pode ser removido após depuração)
        # print(f"  DEBUG PARIDADE RX: Recebido '{frame_bits_str}' ({len(frame_bits_str)} bits)")

        count_ones = frame_bits_str.count('1')
        
        return count_ones % 2 == 0 

    # --- Funções de CRC-32 ---

    def _bits_to_int(self, bits_str: str) -> int:
        """Converte uma string de bits ('0's e '1's) para um inteiro."""
        return int(bits_str, 2)

    def _int_to_bits(self, value: int, num_bits: int) -> str:
        """Converte um inteiro para uma string de bits, preenchendo com zeros à esquerda."""
        return format(value, f'0{num_bits}b')

    def calcular_crc32(self, data_bits_str: str) -> str:
        """
        Calcula o Cyclic Redundancy Check (CRC-32) para uma sequência de bits de entrada.
        A implementação utiliza operações bitwise em inteiros para simular a divisão polinomial.

        Args:
            data_bits_str (str): Uma string contendo '0's e '1's representando os bits de dados.

        Returns:
            str: O CRC-32 calculado como uma string de 32 bits.
        """
        # Converte a string de bits para um inteiro para operações bitwise.
        # O polinômio gerador tem grau 32. Para o cálculo, 'GRAU_CRC32' zeros são anexados
        # ao final dos dados, como se estivessem à esquerda na representação de um número maior.
        dividend = self._bits_to_int(data_bits_str + '0' * self.GRAU_CRC32)
        
        # Converte o polinômio gerador para uma representação que inclui o bit MSB implícito.
        # O polinômio é de grau 32, então ele terá 33 bits quando usado como divisor.
        # Ex: 0x04C11DB7 (32 bits) se torna 1_0000_0100_1100_0000_1000_1110_1101_1011_0111 (33 bits)
        divisor = (1 << self.GRAU_CRC32) | self.CRC32_POLYNOMIAL
        
        # O número de bits no dividendo após adicionar os zeros.
        len_augmented_data = len(data_bits_str) + self.GRAU_CRC32

        # Loop principal da divisão binária.
        # Itera sobre os bits do dividendo, começando do bit mais significativo dos dados originais
        # até o ponto onde o divisor não pode mais ser subtraído (XORed).
        for i in range(len(data_bits_str)): # Itera pelo número de bits de dados originais
            # Verifica se o bit mais significativo da janela atual do dividendo é '1'.
            # A janela é de 'GRAU_CRC32 + 1' bits (33 bits para CRC-32).
            # O bit a ser verificado está na posição `len_augmented_data - 1 - i` (0-indexado).
            if (dividend >> (len_augmented_data - 1 - i)) & 1:
                # Se for '1', realiza a operação XOR com o divisor.
                # O divisor é deslocado para a direita para alinhar com o bit '1' atual.
                # O deslocamento é calculado para que o MSB do divisor alinhe com o bit MSB do dividendo
                # na janela sendo processada.
                shift_amount = len_augmented_data - (self.GRAU_CRC32 + 1) - i
                dividend ^= (divisor << shift_amount)
        
        # O resto da divisão é o CRC. Ele terá 'GRAU_CRC32' bits.
        # Pegamos os últimos 'GRAU_CRC32' bits do resultado.
        crc_result_int = dividend & ((1 << self.GRAU_CRC32) - 1)
        
        # Converte o inteiro CRC de volta para uma string de bits.
        return self._int_to_bits(crc_result_int, self.GRAU_CRC32)

    def adicionar_crc32(self, data_bits_str: str) -> str:
        """
        Calcula o CRC-32 para os bits de dados e os anexa à string de dados.

        Args:
            data_bits_str (str): Uma string contendo '0's e '1's representando os bits de dados.

        Returns:
            str: A string de bits de dados com o CRC-32 anexado ao final.
        """
        crc = self.calcular_crc32(data_bits_str)
        return data_bits_str + crc

    def verificar_crc32(self, frame_bits_str: str) -> bool:
        """
        Verifica a integridade de um quadro (dados + CRC-32) usando o algoritmo CRC-32.
        No receptor, a mensagem completa (dados + CRC) é dividida pelo mesmo polinômio.
        Se o resto da divisão for zero, a mensagem é considerada livre de erros de transmissão.

        Args:
            frame_bits_str (str): Uma string contendo '0's e '1's representando o quadro completo
                                  (dados + CRC).

        Returns:
            bool: True se o resto do cálculo do CRC for zero (nenhum erro detectado).
                  False se o resto for diferente de zero (erro detectado).
        """
        # O quadro deve ter pelo menos o comprimento do CRC para ser válido.
        if len(frame_bits_str) < self.GRAU_CRC32:
            return False 
        
        # Calcula o CRC da mensagem recebida inteira (dados + CRC).
        # Se não houver erros, o resto final deve ser zero.
        
        # Converte a string de bits do quadro para um inteiro para operações bitwise.
        dividend = self._bits_to_int(frame_bits_str)
        divisor = (1 << self.GRAU_CRC32) | self.CRC32_POLYNOMIAL
        
        len_frame = len(frame_bits_str)

        # Itera sobre os bits do quadro, excluindo os bits do próprio CRC para a decisão final.
        # O laço deve ir até o ponto onde o dividendo tem apenas os 'GRAU_CRC32' bits finais.
        for i in range(len_frame - self.GRAU_CRC32):
            if (dividend >> (len_frame - 1 - i)) & 1:
                shift_amount = len_frame - (self.GRAU_CRC32 + 1) - i
                dividend ^= (divisor << shift_amount)
        
        # O resto final deve ser zero para que não haja erros detectados.
        final_remainder = dividend & ((1 << self.GRAU_CRC32) - 1)
        return final_remainder == 0


# --- Funções e Mapeamentos para a opção 'Nenhuma' na detecção de erros ---
# Wrappers para as funções da classe DeteccaoErros
# Estes são mantidos para serem usados diretamente nos mapeamentos para o simulador.

def nenhuma_deteccao_tx(data_bits: str) -> str:
    """
    Função placeholder para o cenário onde nenhuma detecção de erros é aplicada no transmissor (Tx).
    Simplesmente retorna os bits de dados como estão, sem adicionar qualquer redundância de detecção.

    Args:
        data_bits (str): A string de bits de dados a ser transmitida.

    Returns:
        str: A mesma string de bits de dados, sem modificação.
    """
    return data_bits

def nenhuma_deteccao_rx(frame_bits: str) -> bool:
    """
    Função placeholder para o cenário onde nenhuma detecção de erros é aplicada no receptor (Rx).
    Sempre retorna True, indicando que não há um mecanismo de detecção para sinalizar um erro.

    Args:
        frame_bits (str): A string de bits do quadro recebido.

    Returns:
        bool: Sempre True, presumindo ausência de erro quando nenhum mecanismo de detecção é usado.
    """
    return True 


# Mapeamento de protocolos para uso no simulador (facilita a seleção via GUI)
# Cada chave corresponde a uma opção de protocolo na GUI, e o valor é a função a ser chamada.
# A instância da classe DeteccaoErros é criada aqui para que os métodos possam ser referenciados.
_deteccao_erros_instance = DeteccaoErros()

DETECCAO_ERROS_TX = {
    'Bit de paridade par': _deteccao_erros_instance.adicionar_paridade_par,
    'CRC-32': _deteccao_erros_instance.adicionar_crc32,
    'Nenhuma': nenhuma_deteccao_tx
}

DETECCAO_ERROS_RX = {
    'Bit de paridade par': _deteccao_erros_instance.verificar_paridade_par,
    'CRC-32': _deteccao_erros_instance.verificar_crc32,
    'Nenhuma': nenhuma_deteccao_rx
}