# CamadaEnlace/deteccao_erros.py
class ErrorDetector:
    """Implementa métodos para detecção de erros."""

    def __init__(self):
        # Polinômio padrão para CRC-32 (IEEE 802.3), incluindo o termo x^32 implícito
        self.CRC32_POLY = 0x104C11DB7

    def add_even_parity(self, bit_chunk):
        """Adiciona um bit de paridade para garantir que o número total de '1's seja par."""
        return bit_chunk + ('1' if bit_chunk.count('1') % 2 != 0 else '0')

    def check_even_parity(self, chunk_with_parity):
        """Verifica se o número total de '1's no bloco é par."""
        return chunk_with_parity.count('1') % 2 == 0

    def _crc_division_engine(self, data_bits_str, poly_bits_str):
        """
        Motor de divisão CRC (XOR) que opera sobre os dados já preparados.
        Não adiciona padding.
        """
        poly = list(map(int, poly_bits_str))
        data = list(map(int, data_bits_str))
        n = len(poly)

        for i in range(len(data) - n + 1):
            if data[i] == 1:
                for j in range(n):
                    data[i+j] ^= poly[j]
        
        remainder = "".join(map(str, data[-(n-1):]))
        return remainder

    def generate_crc(self, data_bits):
        """Gera o checksum CRC-32 para os dados. Adiciona padding de zeros antes da divisão."""
        poly_bits = bin(self.CRC32_POLY)[2:]
        num_poly_bits = len(poly_bits)
        
        padded_data = data_bits + '0' * (num_poly_bits - 1)
        
        remainder = self._crc_division_engine(padded_data, poly_bits)
        
        return remainder.zfill(num_poly_bits - 1)

    def check_crc(self, frame_with_crc):
        """
        Verifica a integridade de um quadro (dados + crc) usando CRC-32.
        Retorna o valor inteiro do resto. O valor esperado é 0.
        """
        poly_bits = bin(self.CRC32_POLY)[2:]
        
        remainder_str = self._crc_division_engine(frame_with_crc, poly_bits)
        
        return int(remainder_str, 2)