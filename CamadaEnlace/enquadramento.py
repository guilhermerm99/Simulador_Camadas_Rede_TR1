# CamadaEnlace/enquadramento.py

class Enquadramento:
    """
    Implementa protocolos de enquadramento de dados para a camada de enlace.
    Suporta Contagem de Caracteres, Enquadramento com FLAGS e inserção de bytes (Byte Stuffing),
    e Enquadramento com FLAGS e inserção de bits (Bit Stuffing).
    """

    # --- Constantes para Enquadramento ---
    # FLAG_BYTE: Usado para delimitar quadros em enquadramento por bytes.
    # Representa a sequência de bits '01111110'.
    FLAG_BYTE = b'\x7E' 
    
    # ESC_BYTE: Usado como caractere de escape em byte stuffing.
    # Exemplo: Data Link Escape (DLE), ASCII 0x10, ou Device Control 1 (DC1), ASCII 0x11.
    # Escolha 0x1B (ESC) para evitar conflitos comuns, ou 0x10 (DLE) que é mais comum em HDLC.
    ESC_BYTE = b'\x10' # Usando DLE (Data Link Escape)

    # FLAG_BIT_STR: String de bits para delimitar quadros em enquadramento por bits.
    # Corresponde à sequência de bits da FLAG_BYTE.
    FLAG_BIT_STR = '01111110'

    # Sequência de bits que dispara o bit stuffing (cinco '1's consecutivos)
    BIT_STUFF_SEQUENCE = '11111'
    # Bit a ser inserido após a sequência de stuffing
    STUFFING_BIT = '0'


    def __init__(self):
        """Inicializa a classe Enquadramento."""
        pass

    # --- Enquadramento por Contagem de Caracteres ---
    def aplicar_enquadramento_contagem_caracteres(self, data_bits: str) -> str:
        """
        Aplica enquadramento por contagem de caracteres.
        Adiciona um cabeçalho de 8 bits que representa o número de bytes no payload.
        Assume que a string de bits de entrada `data_bits` será tratada como bytes para a contagem.
        Se o comprimento não for múltiplo de 8, zeros são adicionados como padding.

        Args:
            data_bits (str): Uma string contendo '0's e '1's representando os dados.

        Returns:
            str: O quadro com o cabeçalho de comprimento e o payload (incluindo padding).

        Raises:
            ValueError: Se o payload for muito grande para ser representado por 8 bits (max 255 bytes).
        """
        # Garante que data_bits tem um comprimento múltiplo de 8 para formar bytes completos.
        # Adiciona zeros à direita (padding) se necessário.
        padding_len = (8 - len(data_bits) % 8) % 8
        padded_data_bits = data_bits + '0' * padding_len

        # Calcula o número de bytes no payload.
        # len(padded_data_bits) / 8 é o número de bytes.
        num_bytes_payload = len(padded_data_bits) // 8

        if num_bytes_payload > 255:
            raise ValueError(f"Payload de {num_bytes_payload} bytes excede o limite (255) para enquadramento por contagem de caracteres.")

        # Converte o número de bytes para uma string de 8 bits (cabeçalho).
        length_header_bits = format(num_bytes_payload, '08b')

        # O quadro é o cabeçalho de comprimento seguido pelos bits do payload (com padding).
        return length_header_bits + padded_data_bits

    def remover_enquadramento_contagem_caracteres(self, frame_bits: str) -> str:
        """
        Remove o enquadramento por contagem de caracteres de um quadro.
        Extrai o cabeçalho de comprimento e usa-o para determinar o payload.
        Remove qualquer padding que tenha sido adicionado.

        Args:
            frame_bits (str): Uma string contendo '0's e '1's representando o quadro completo.

        Returns:
            str: A string de bits dos dados originais (sem o cabeçalho e sem padding).

        Raises:
            ValueError: Se o quadro for muito curto para conter um cabeçalho de comprimento.
        """
        if len(frame_bits) < 8:
            raise ValueError("Quadro muito curto para enquadramento por contagem de caracteres (requer pelo menos 8 bits para o cabeçalho).")

        # Extrai o cabeçalho de 8 bits que indica o comprimento do payload em bytes.
        length_header_bits = frame_bits[:8]
        # O restante da string são os bits do payload (com possível padding).
        payload_with_padding_bits = frame_bits[8:]

        # Converte o cabeçalho de volta para um inteiro para obter o comprimento esperado.
        num_bytes_expected = int(length_header_bits, 2)
        expected_payload_len_bits = num_bytes_expected * 8

        # Verifica se o comprimento real do payload recebido corresponde ao esperado.
        if len(payload_with_padding_bits) < expected_payload_len_bits:
            # Se o quadro foi truncado ou o cabeçalho está incorreto devido a erros,
            # pode-se levantar um erro ou retornar a parte disponível.
            # Para robustez da simulação, vamos retornar a parte disponível,
            # mas em um sistema real, isso indicaria um erro grave de quadro.
            print(f"Aviso: Comprimento do payload recebido ({len(payload_with_padding_bits)} bits) é menor que o esperado ({expected_payload_len_bits} bits).")
            # Retorna o que foi recebido até o comprimento esperado ou o que tiver.
            return payload_with_padding_bits 
        
        # Retorna apenas os bits de dados, removendo o padding e o cabeçalho.
        # Assumimos que o padding são zeros e não fazem parte do dado útil.
        return payload_with_padding_bits[:expected_payload_len_bits]


    # --- Enquadramento com FLAGS e Inserção de Bytes (Byte Stuffing) ---
    def aplicar_enquadramento_flags_bytes(self, data_bytes: bytes) -> bytes:
        """
        Aplica enquadramento com FLAGS e inserção de bytes (byte stuffing).
        Adiciona FLAG_BYTE no início e fim do quadro.
        No payload, todas as ocorrências de FLAG_BYTE e ESC_BYTE são 'escapadas'
        (precedidas por um ESC_BYTE extra).

        Args:
            data_bytes (bytes): A sequência de bytes de dados a ser enquadrada.

        Returns:
            bytes: O quadro enquadrado com FLAGS e bytes de stuffing.
        """
        # Primeiro, escapa o próprio ESC_BYTE para evitar ambiguidades.
        # Onde quer que ESC_BYTE apareça no dado, ele se torna ESC_BYTE + ESC_BYTE.
        stuffed_data = data_bytes.replace(self.ESC_BYTE, self.ESC_BYTE + self.ESC_BYTE)
        
        # Em seguida, escapa o FLAG_BYTE.
        # Onde quer que FLAG_BYTE apareça no dado (agora com ESC_BYTEs escapados),
        # ele se torna ESC_BYTE + FLAG_BYTE.
        stuffed_data = stuffed_data.replace(self.FLAG_BYTE, self.ESC_BYTE + self.FLAG_BYTE)
        
        # O quadro final é a FLAG de início, os dados escapados, e a FLAG de fim.
        return self.FLAG_BYTE + stuffed_data + self.FLAG_BYTE

    def remover_enquadramento_flags_bytes(self, frame_bytes: bytes) -> bytes:
        """
        Remove enquadramento com FLAGS e inserção de bytes (byte stuffing).
        Primeiro, remove as FLAGS de início e fim.
        Em seguida, reverte o processo de escape, removendo os ESC_BYTEs adicionados.

        Args:
            frame_bytes (bytes): O quadro completo em bytes, incluindo FLAGS e stuffing.

        Returns:
            bytes: A sequência de bytes de dados originais (sem FLAGS e stuffing).

        Raises:
            ValueError: Se o quadro não começar ou terminar com a FLAG_BYTE esperada.
            ValueError: Se o quadro for muito curto (não contendo pelo menos as duas FLAGS).
        """
        if len(frame_bytes) < len(self.FLAG_BYTE) * 2:
            raise ValueError("Quadro muito curto para conter FLAGS de início e fim.")

        if not (frame_bytes.startswith(self.FLAG_BYTE) and frame_bytes.endswith(self.FLAG_BYTE)):
            raise ValueError("Quadro não começa ou termina com a FLAG_BYTE esperada.")

        # Remove as FLAGS de início e fim para obter apenas o payload com stuffing.
        data_with_stuffing = frame_bytes[len(self.FLAG_BYTE):-len(self.FLAG_BYTE)]

        # Desescapa o FLAG_BYTE: ESC_BYTE + FLAG_BYTE volta a ser FLAG_BYTE.
        unstuffed_data = data_with_stuffing.replace(self.ESC_BYTE + self.FLAG_BYTE, self.FLAG_BYTE)
        
        # Desescapa o ESC_BYTE: ESC_BYTE + ESC_BYTE volta a ser ESC_BYTE.
        unstuffed_data = unstuffed_data.replace(self.ESC_BYTE + self.ESC_BYTE, self.ESC_BYTE)
        
        return unstuffed_data


    # --- Enquadramento com FLAGS e Inserção de Bits (Bit Stuffing) ---
    def aplicar_enquadramento_flags_bits(self, data_bits: str) -> str:
        """
        Aplica enquadramento com FLAGS e inserção de bits (bit stuffing).
        Adiciona FLAG_BIT_STR no início e fim do quadro.
        Dentro do payload, um bit '0' é inserido após cada sequência de cinco '1's consecutivos.
        Isso evita que a sequência de FLAG (01111110) apareça acidentalmente nos dados.

        Args:
            data_bits (str): Uma string contendo '0's e '1's representando os dados.

        Returns:
            str: O quadro enquadrado com FLAGS e bits de stuffing.
        """
        stuffed_data = ""
        count_ones = 0
        for bit in data_bits:
            if bit == '1':
                count_ones += 1
                stuffed_data += '1'
                if count_ones == 5:
                    # Após 5 '1's consecutivos, insere um '0' (bit de stuffing)
                    stuffed_data += self.STUFFING_BIT
                    count_ones = 0 # Reinicia a contagem de '1's
            else: # bit == '0'
                stuffed_data += '0'
                count_ones = 0 # Reinicia a contagem de '1's ao encontrar um '0'
        
        # Adiciona as FLAGS no início e fim do payload com stuffing.
        return self.FLAG_BIT_STR + stuffed_data + self.FLAG_BIT_STR

    def remover_enquadramento_flags_bits(self, frame_bits: str) -> str:
        """
        Remove enquadramento com FLAGS e inserção de bits (bit stuffing).
        Primeiro, remove as FLAGS de início e fim.
        Em seguida, reverte o processo de stuffing, removendo os bits '0' que foram inseridos
        após sequências de cinco '1's consecutivos.

        Args:
            frame_bits (str): Uma string contendo '0's e '1's representando o quadro completo.

        Returns:
            str: A string de bits dos dados originais (sem FLAGS e stuffing).

        Raises:
            ValueError: Se o quadro não começar ou terminar com a FLAG_BIT_STR esperada.
            ValueError: Se o quadro for muito curto (não contendo pelo menos as duas FLAGS).
            ValueError: Se o quadro contiver uma sequência inválida de bits (ex: mais de 5 '1's
                        sem um '0' de stuffing onde deveria haver, indicando um erro).
        """
        if len(frame_bits) < len(self.FLAG_BIT_STR) * 2:
            raise ValueError("Quadro muito curto para conter FLAGS de início e fim.")

        if not (frame_bits.startswith(self.FLAG_BIT_STR) and frame_bits.endswith(self.FLAG_BIT_STR)):
            raise ValueError("Quadro não começa ou termina com a FLAG_BIT_STR esperada.")

        # Remove as FLAGS de início e fim para obter apenas o payload com stuffing.
        data_with_stuffing = frame_bits[len(self.FLAG_BIT_STR):-len(self.FLAG_BIT_STR)]

        unstuffed_data = ""
        count_ones = 0
        
        # Percorre o payload com stuffing para remover os bits de stuffing.
        for bit in data_with_stuffing:
            if bit == '1':
                count_ones += 1
                unstuffed_data += '1'
                if count_ones > 5:
                    # Isso indica um erro no quadro, pois não deveria haver mais de 5 '1's
                    # consecutivos sem um '0' de stuffing no payload.
                    raise ValueError(f"Erro de bit stuffing: Mais de 5 '1's consecutivos sem '0' (sequência de {count_ones} uns). Provável erro no quadro.")
            elif bit == '0':
                if count_ones == 5:
                    # Este '0' é um bit de stuffing, ele deve ser IGNORADO (não adicionado ao unstuffed_data).
                    # Reinicia a contagem de '1's após remover o bit de stuffing.
                    count_ones = 0 
                else:
                    # Este '0' é um bit de dado original (não foi precedido por 5 '1's).
                    unstuffed_data += '0'
                    count_ones = 0 # Reinicia a contagem de '1's ao encontrar um '0' de dado
            else:
                raise ValueError("Quadro contém caracteres inválidos (não bits '0' ou '1').")
                
        return unstuffed_data


# --- Mapeamento de protocolos para uso no simulador ---
# Cria uma instância da classe Enquadramento.
_enquadramento_instance = Enquadramento()

ENQUADRAMENTO_TX = {
    'Contagem de caracteres': _enquadramento_instance.aplicar_enquadramento_contagem_caracteres,
    'FLAGS e inserção de bytes': _enquadramento_instance.aplicar_enquadramento_flags_bytes,
    'FLAGS e inserção de bits': _enquadramento_instance.aplicar_enquadramento_flags_bits
}

ENQUADRAMENTO_RX = {
    'Contagem de caracteres': _enquadramento_instance.remover_enquadramento_contagem_caracteres,
    'FLAGS e inserção de bytes': _enquadramento_instance.remover_enquadramento_flags_bytes,
    'FLAGS e inserção de bits': _enquadramento_instance.remover_enquadramento_flags_bits
}