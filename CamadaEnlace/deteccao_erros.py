# CamadaEnlace/deteccao_erros.py

class ErrorDetector:
    """Implementa métodos para detecção de erros."""

    def __init__(self):
        self.CRC32_POLY = 0x04C11DB7

    def add_even_parity(self, bit_chunk):
        return bit_chunk + ('1' if bit_chunk.count('1') % 2 != 0 else '0')

    def check_even_parity(self, chunk_with_parity):
        return chunk_with_parity.count('1') % 2 == 0

    def _crc32_manual_division(self, data_bits):
        poly_bits = bin(self.CRC32_POLY)[2:]
        n = len(poly_bits)
        data_padded = list(map(int, data_bits + '0' * (n - 1)))
        poly = list(map(int, poly_bits))

        for i in range(len(data_bits)):
            if data_padded[i] == 1:
                for j in range(n):
                    data_padded[i+j] ^= poly[j]
        
        remainder = "".join(map(str, data_padded[len(data_bits):]))
        return remainder

    def generate_crc(self, data_bits):
        """Gera o checksum CRC-32 para os dados."""
        remainder = self._crc32_manual_division(data_bits)
        # <<< INÍCIO DA CORREÇÃO >>>
        # Garante que a string binária do CRC tenha sempre 32 bits, preenchendo com zeros à esquerda.
        return remainder.zfill(32)
        # <<< FIM DA CORREÇÃO >>>

    def check_crc(self, frame_with_crc):
        """Verifica a integridade dos dados usando CRC-32."""
        remainder = self._crc32_manual_division(frame_with_crc)
        return int(remainder, 2) == 0