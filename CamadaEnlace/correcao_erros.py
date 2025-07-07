class ErrorCorrector:
    """Implementa o Código de Hamming(7,4) para correção de erro de 1 bit por bloco.
    Atua na Camada de Enlace, adicionando e utilizando bits de paridade para garantir integridade dos dados.
    """

    def encode_hamming(self, data_bits):
        """
        Codifica uma sequência de bits usando Hamming(7,4), adicionando 3 bits de paridade
        a cada grupo de 4 bits de dados. Permite a correção de erro de bit único.
        Retorna uma string com os blocos codificados concatenados.
        """
        encoded_string = ""
        
        for i in range(0, len(data_bits), 4):
            chunk = data_bits[i:i+4].ljust(4, '0')  # Garante 4 bits no bloco, completando com '0' se necessário
            d = [int(b) for b in chunk]  # Converte os bits em inteiros para cálculo

            # Cálculo dos bits de paridade (p1, p2, p3) conforme Hamming(7,4)
            p1 = (d[0] + d[1] + d[3]) % 2  # Verifica posições 1,3,5,7
            p2 = (d[0] + d[2] + d[3]) % 2  # Verifica posições 2,3,6,7
            p3 = (d[1] + d[2] + d[3]) % 2  # Verifica posições 4,5,6,7

            # Formato do bloco codificado: p1 p2 d1 p3 d2 d3 d4
            encoded_chunk = f"{p1}{p2}{d[0]}{p3}{d[1]}{d[2]}{d[3]}"
            encoded_string += encoded_chunk
        
        return encoded_string

    def decode_hamming(self, received_bits):
        """
        Decodifica blocos Hamming(7,4), detectando e corrigindo 1 erro de bit por bloco.
        Retorna:
        - decoded_string: dados extraídos sem os bits de paridade
        - corrected_full_frame: bits completos corrigidos, com paridade
        - report: string com estatísticas de correções realizadas
        """
        decoded_string = ""
        corrected_full_frame = ""
        erros_corrigidos = 0
        
        for i in range(0, len(received_bits), 7):
            chunk = received_bits[i:i+7]
            if len(chunk) < 7: continue  # Ignora blocos incompletos

            bits = [int(b) for b in chunk]
            p1, p2, d1, p3, d2, d3, d4 = bits  # Mapeia posições do bloco

            # Cálculo da síndrome (c1, c2, c3) para detectar a posição do erro (se houver)
            c1 = (p1 + d1 + d2 + d4) % 2
            c2 = (p2 + d1 + d3 + d4) % 2
            c3 = (p3 + d2 + d3 + d4) % 2

            # Conversão da síndrome em posição de erro (0 = sem erro)
            error_pos = c3 * 4 + c2 * 2 + c1

            chunk_list = list(chunk)
            if error_pos != 0:
                erros_corrigidos += 1
                # Corrige o bit invertendo-o na posição detectada (1-indexado)
                chunk_list[error_pos - 1] = '1' if chunk_list[error_pos - 1] == '0' else '0'

            corrected_chunk_str = "".join(chunk_list)
            corrected_full_frame += corrected_chunk_str

            # Extração dos dados: posições 3, 5, 6, 7 do bloco (d1, d2, d3, d4)
            decoded_string += corrected_chunk_str[2] + corrected_chunk_str[4:]

        # Relatório de correções realizadas
        if erros_corrigidos > 0:
            report = f"{erros_corrigidos} erro(s) de bit único corrigido(s)."
        else:
            report = "Nenhum erro de bit único detectado."
        
        return decoded_string, corrected_full_frame, report
