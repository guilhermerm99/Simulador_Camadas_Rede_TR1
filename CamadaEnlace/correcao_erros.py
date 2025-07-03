# CamadaEnlace/correcao_erros.py

class ErrorCorrector:
    """Implementa o Código de Hamming para correção de erro único."""

    def encode_hamming(self, data_bits):
        """Codifica dados usando Hamming(7,4)."""
        encoded_string = ""
        for i in range(0, len(data_bits), 4):
            chunk = data_bits[i:i+4].ljust(4, '0')
            d = [int(b) for b in chunk]
            p1 = (d[0] + d[1] + d[3]) % 2
            p2 = (d[0] + d[2] + d[3]) % 2
            p3 = (d[1] + d[2] + d[3]) % 2
            encoded_chunk = f"{p1}{p2}{d[0]}{p3}{d[1]}{d[2]}{d[3]}"
            encoded_string += encoded_chunk
        return encoded_string

    # <<< INÍCIO DA MUDANÇA >>>
    def decode_hamming(self, received_bits):
        """
        Decodifica e corrige um erro único por bloco usando Hamming(7,4).
        Retorna:
        1. decoded_string: Os bits de dados puros, sem paridade.
        2. corrected_full_frame: O quadro Hamming completo após a tentativa de correção.
        3. report: Um relatório em texto sobre as correções feitas.
        """
        decoded_string = ""
        corrected_full_frame = ""
        erros_corrigidos = 0
        
        for i in range(0, len(received_bits), 7):
            chunk = received_bits[i:i+7]
            if len(chunk) < 7: continue

            bits = [int(b) for b in chunk]
            p1, p2, d1, p3, d2, d3, d4 = bits
            
            c1 = (p1 + d1 + d2 + d4) % 2
            c2 = (p2 + d1 + d3 + d4) % 2
            c3 = (p3 + d2 + d3 + d4) % 2
            error_pos = c3 * 4 + c2 * 2 + c1
            
            chunk_list = list(chunk)
            if error_pos != 0:
                erros_corrigidos += 1
                chunk_list[error_pos-1] = '1' if chunk_list[error_pos-1] == '0' else '0'

            corrected_chunk_str = "".join(chunk_list)
            corrected_full_frame += corrected_chunk_str
            # Extrai os bits de dados puros do quadro JÁ CORRIGIDO
            decoded_string += corrected_chunk_str[2] + corrected_chunk_str[4:]
        
        if erros_corrigidos > 0:
            report = f"{erros_corrigidos} erro(s) de bit único corrigido(s)."
        else:
            report = "Nenhum erro de bit único detectado."
            
        return decoded_string, corrected_full_frame, report
    # <<< FIM DA MUDANÇA >>>