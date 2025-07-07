class ErrorDetector:
    """
    Implementa métodos de detecção de erros na Camada de Enlace.
    Inclui Paridade Par (detecta 1 bit de erro) e CRC-32 (detecta erros em rajada).
    """

    def __init__(self):
        # Polinômio CRC-32 (IEEE 802.3), utilizado em protocolos como Ethernet.
        # Representado sem o bit mais significativo (x^32), que é implícito.
        self.CRC32_POLY = 0x104C11DB7

    def add_even_parity(self, bit_chunk):
        """
        Aplica Paridade Par: adiciona 1 bit no final do bloco, garantindo que a
        quantidade total de bits '1' seja par.
        Método simples para detectar erro de 1 bit na transmissão.
        """
        return bit_chunk + ('1' if bit_chunk.count('1') % 2 != 0 else '0')

    def check_even_parity(self, chunk_with_parity):
        """
        Verifica se a paridade está correta (número par de '1's).
        Retorna True se o bloco for considerado íntegro, ou False se houver erro.
        Utilizado na recepção.
        """
        return chunk_with_parity.count('1') % 2 == 0

    def _crc_division_engine(self, data_bits_str, poly_bits_str):
        """
        Executa a divisão polinomial binária (modulo-2) entre os dados e o polinômio.
        Essa operação simula a divisão binária sem transporte (usa XOR).
        É a base do cálculo e verificação do CRC.
        """
        poly = list(map(int, poly_bits_str))
        data = list(map(int, data_bits_str))
        n = len(poly)

        # Percorre os bits dos dados, aplicando XOR com o polinômio quando encontra '1'
        for i in range(len(data) - n + 1):
            if data[i] == 1:
                for j in range(n):
                    data[i + j] ^= poly[j]

        # Retorna o resto da divisão (CRC) como string binária
        remainder = "".join(map(str, data[-(n - 1):]))
        return remainder

    def generate_crc(self, data_bits):
        """
        Gera o valor do CRC-32 com base nos dados binários informados.
        É utilizado no transmissor para anexar o código de redundância ao final do quadro.
        """
        poly_bits = bin(self.CRC32_POLY)[2:]  # Converte o polinômio para binário
        num_poly_bits = len(poly_bits)

        # Adiciona zeros ao final dos dados (padding) para preparar a divisão polinomial
        padded_data = data_bits + '0' * (num_poly_bits - 1)

        # Executa a divisão para obter o valor do CRC (resto da operação)
        remainder = self._crc_division_engine(padded_data, poly_bits)

        # Garante que o CRC tenha o tamanho correto, adicionando zeros à esquerda se necessário
        return remainder.zfill(num_poly_bits - 1)

    def check_crc(self, frame_with_crc):
        """
        Verifica se um quadro (dados + CRC) possui integridade.
        É aplicado no receptor. Se o resto da divisão for zero, não há erro.
        """
        poly_bits = bin(self.CRC32_POLY)[2:]
        remainder_str = self._crc_division_engine(frame_with_crc, poly_bits)
        return int(remainder_str, 2)  # Retorna 0 se não houver erro
