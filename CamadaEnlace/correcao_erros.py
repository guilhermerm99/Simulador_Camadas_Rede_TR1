class ErrorCorrector:
    """Implementa o Código de Hamming(7,4) para correção de erro de 1 bit por bloco.
    Atua na Camada de Enlace, adicionando e utilizando bits de paridade para garantir integridade dos dados.
    """

    def encode_hamming(self, data_bits):
        """
        Aplica codificação Hamming(7,4) nos dados binários recebidos.
        A cada 4 bits de informação, são adicionados 3 bits de paridade para formar blocos de 7 bits.
        Essa estrutura permite a correção de erros de bit único na recepção.
        """
        encoded_string = ""

        for i in range(0, len(data_bits), 4):
            chunk = data_bits[i:i+4].ljust(4, '0')  # Preenche com '0' se o bloco tiver menos de 4 bits
            d = [int(b) for b in chunk]  # Converte os bits de caractere para inteiros

            # Calcula os bits de paridade com base nas posições do código Hamming(7,4)
            p1 = (d[0] + d[1] + d[3]) % 2  # Paridade para posições 1, 3, 5, 7
            p2 = (d[0] + d[2] + d[3]) % 2  # Paridade para posições 2, 3, 6, 7
            p3 = (d[1] + d[2] + d[3]) % 2  # Paridade para posições 4, 5, 6, 7

            # Monta o bloco codificado na ordem: p1 p2 d1 p3 d2 d3 d4
            encoded_chunk = f"{p1}{p2}{d[0]}{p3}{d[1]}{d[2]}{d[3]}"
            encoded_string += encoded_chunk

        return encoded_string

    def decode_hamming(self, received_bits):
        """
        Decodifica os blocos Hamming(7,4), detectando e corrigindo 1 erro de bit por bloco.
        Retorna:
        - decoded_string: sequência de dados puros (sem bits de paridade)
        - corrected_full_frame: bits recebidos com possíveis correções aplicadas
        - report: resumo da quantidade de erros detectados e corrigidos
        """
        decoded_string = ""
        corrected_full_frame = ""
        erros_corrigidos = 0

        for i in range(0, len(received_bits), 7):
            chunk = received_bits[i:i+7]
            if len(chunk) < 7:
                continue  # Ignora blocos incompletos (caso final da string não feche em múltiplo de 7)

            bits = [int(b) for b in chunk]
            p1, p2, d1, p3, d2, d3, d4 = bits  # Mapeamento direto dos bits do bloco Hamming

            # Cálculo dos bits de síndrome (c1, c2, c3), que indicam a posição do erro (se houver)
            c1 = (p1 + d1 + d2 + d4) % 2  # Verifica paridade no conjunto correspondente ao bit 1
            c2 = (p2 + d1 + d3 + d4) % 2  # Verifica paridade para bit 2
            c3 = (p3 + d2 + d3 + d4) % 2  # Verifica paridade para bit 4

            # Determina a posição do erro no bloco (1 a 7), ou 0 se não houver erro
            error_pos = c3 * 4 + c2 * 2 + c1

            chunk_list = list(chunk)
            if error_pos != 0:
                erros_corrigidos += 1
                # Inverte o bit incorreto para corrigir o erro (posição 1-indexada)
                chunk_list[error_pos - 1] = '1' if chunk_list[error_pos - 1] == '0' else '0'

            corrected_chunk_str = "".join(chunk_list)
            corrected_full_frame += corrected_chunk_str

            # Extrai os bits de dados das posições 3, 5, 6, 7 (d1, d2, d3, d4)
            decoded_string += corrected_chunk_str[2] + corrected_chunk_str[4:]

        # Gera um relatório simples da quantidade de erros de bit único corrigidos
        if erros_corrigidos > 0:
            report = f"{erros_corrigidos} erro(s) de bit único corrigido(s)."
        else:
            report = "Nenhum erro de bit único detectado."

        return decoded_string, corrected_full_frame, report
