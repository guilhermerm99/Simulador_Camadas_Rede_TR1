class ErrorDetector:
    """
    Implementa métodos de detecção de erros na Camada de Enlace.
    Inclui Paridade Par (erro de 1 bit) e CRC-32 (erro em rajada).
    """

    def __init__(self):
        # Polinômio CRC-32 (IEEE 802.3) usado em redes Ethernet.
        # O bit x^32 é implícito e omitido na forma hexadecimal.
        self.CRC32_POLY = 0x104C11DB7

    def add_even_parity(self, bit_chunk):
        """
        Adiciona bit de paridade par ao final do bloco de bits.
        Garante que o número total de bits '1' seja par.
        Técnica simples usada na Camada de Enlace para detectar erro de 1 bit.
        """
        return bit_chunk + ('1' if bit_chunk.count('1') % 2 != 0 else '0')

    def check_even_parity(self, chunk_with_parity):
        """
        Verifica se o total de '1's (incluindo o bit de paridade) é par.
        Retorna True se não houver erro (paridade correta), ou False se houver erro.
        Aplica-se no receptor.
        """
        return chunk_with_parity.count('1') % 2 == 0

    def _crc_division_engine(self, data_bits_str, poly_bits_str):
        """
        Realiza a divisão polinomial binária (XOR) entre os dados e o polinômio gerador.
        Utilizado internamente para cálculo e verificação de CRC na Camada de Enlace.
        """
        poly = list(map(int, poly_bits_str))
        data = list(map(int, data_bits_str))
        n = len(poly)

        # Percorre os bits dos dados, realizando XOR com o polinômio se o bit atual for 1
        for i in range(len(data) - n + 1):
            if data[i] == 1:
                for j in range(n):
                    data[i + j] ^= poly[j]

        # Retorna o resto da divisão (CRC), como string binária
        remainder = "".join(map(str, data[-(n - 1):]))
        return remainder

    def generate_crc(self, data_bits):
        """
        Gera o CRC-32 para os dados usando o polinômio padrão.
        Essa função é aplicada no transmissor da Camada de Enlace.
        """
        poly_bits = bin(self.CRC32_POLY)[2:]
        num_poly_bits = len(poly_bits)

        # Adiciona zeros (padding) ao final dos dados para o cálculo do CRC
        padded_data = data_bits + '0' * (num_poly_bits - 1)

        # Executa divisão polinomial para obter o CRC (resto)
        remainder = self._crc_division_engine(padded_data, poly_bits)

        # Retorna o CRC com padding à esquerda para manter o tamanho correto
        return remainder.zfill(num_poly_bits - 1)

    def check_crc(self, frame_with_crc):
        """
        Verifica se o quadro completo (dados + CRC) está íntegro.
        Aplicado no receptor da Camada de Enlace.
        Se o resto da divisão for zero, o quadro é considerado livre de erros.
        """
        poly_bits = bin(self.CRC32_POLY)[2:]
        remainder_str = self._crc_division_engine(frame_with_crc, poly_bits)
        return int(remainder_str, 2)
