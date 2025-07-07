import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)  # Pode ser ajustado conforme o nível de detalhamento desejado (DEBUG, INFO, etc.)

class Framer:
    """Gerencia técnicas de enquadramento de dados na Camada de Enlace.
    Implementa:
    - Contagem de caracteres
    - Byte stuffing
    - Bit stuffing
    """

    FLAG_BIT_PATTERN = "01111110"  # Delimitador de quadro usado em bit stuffing (padrão HDLC)
    FLAG_BYTE = 0x7E               # 01111110 em decimal (126), usado em byte stuffing
    ESC_BYTE = 0x7D                # Byte de escape (125) para marcar FLAG ou ESC no payload

    def frame_char_count(self, payload_bits):
        """
        Enquadra os dados usando a técnica de contagem de caracteres:
        - Insere um cabeçalho de 8 bits representando o número de bytes do payload.
        - Técnica simples e eficiente, mas sensível a erros no cabeçalho.
        """
        logger.debug(f"frame_char_count: entrada payload_bits len={len(payload_bits)}")
        if len(payload_bits) % 8 != 0:
            # Preenche o payload com zeros para garantir múltiplo de 8 bits (1 byte)
            padding = 8 - (len(payload_bits) % 8)
            payload_bits += '0' * padding
            logger.debug(f"frame_char_count: adicionado padding de {padding} bits")

        num_bytes = len(payload_bits) // 8
        if num_bytes > 255:
            # Limite do cabeçalho de 8 bits atingido (valor máximo: 255)
            logger.error("frame_char_count: Payload excede o tamanho máximo de 255 bytes")
            raise ValueError("Payload excede o tamanho máximo de 255 bytes.")
        
        header = format(num_bytes, '08b')  # Cabeçalho binário com o número de bytes
        frame = header + payload_bits
        logger.debug(f"frame_char_count: saída frame len={len(frame)}")
        return frame

    def deframe_char_count(self, frame_bits):
        """
        Desfaz o enquadramento por contagem de caracteres:
        - Lê o cabeçalho para saber quantos bytes compõem o payload.
        - Retorna o payload original e os bits restantes do quadro (se houver).
        """
        logger.debug(f"deframe_char_count: entrada frame_bits len={len(frame_bits)}")
        header_bits = frame_bits[:8]
        payload_len_in_bytes = int(header_bits, 2)
        payload_len_in_bits = payload_len_in_bytes * 8

        payload = frame_bits[8 : 8 + payload_len_in_bits]
        remaining_frame = frame_bits[8 + payload_len_in_bits:]
        logger.debug(f"deframe_char_count: payload len={len(payload)}, restante len={len(remaining_frame)}")
        return payload, remaining_frame

    def frame_byte_stuffing(self, payload_bits):
        """
        Enquadra os dados usando byte stuffing:
        - Converte bits em bytes.
        - Adiciona FLAG no início e fim do quadro.
        - Insere ESC antes de qualquer FLAG ou ESC presente no payload.
        """
        logger.debug(f"frame_byte_stuffing: entrada payload_bits len={len(payload_bits)}")
        padding_needed = len(payload_bits) % 8
        if padding_needed != 0:
            # Preenche com zeros até formar múltiplos de 8 bits
            num_zeros_to_add = 8 - padding_needed
            payload_bits += '0' * num_zeros_to_add
            logger.debug(f"frame_byte_stuffing: adicionado {num_zeros_to_add} bits de padding para alinhamento em bytes")

        payload_bytes = [int(payload_bits[i:i+8], 2) for i in range(0, len(payload_bits), 8)]
        logger.debug(f"frame_byte_stuffing: convertido em {len(payload_bytes)} bytes")

        stuffed_payload = []
        for byte in payload_bytes:
            # Verifica se o byte é um caractere de controle (FLAG ou ESC)
            if byte == self.FLAG_BYTE or byte == self.ESC_BYTE:
                stuffed_payload.append(self.ESC_BYTE)  # Insere escape antes
                logger.debug(f"frame_byte_stuffing: byte {byte:#04x} escapado")
            stuffed_payload.append(byte)

        # Adiciona FLAG no início e fim para delimitar o quadro
        final_frame_bytes = [self.FLAG_BYTE] + stuffed_payload + [self.FLAG_BYTE]
        frame_bits = "".join(format(byte, '08b') for byte in final_frame_bytes)
        logger.debug(f"frame_byte_stuffing: saída frame_bits len={len(frame_bits)}")
        return frame_bits

    def deframe_byte_stuffing(self, frame_bits):
        """
        Remove o enquadramento feito por byte stuffing:
        - Verifica se o quadro começa e termina com a FLAG.
        - Remove bytes de escape (ESC) inseridos antes de FLAG ou ESC originais.
        """
        logger.debug(f"deframe_byte_stuffing: entrada frame_bits len={len(frame_bits)}")

        if len(frame_bits) % 8 != 0:
            logger.error("deframe_byte_stuffing: erro - frame_bits não é múltiplo de 8")
            return None, "Erro de enquadramento: comprimento inválido (não múltiplo de 8)."
        if not frame_bits.startswith(self.FLAG_BIT_PATTERN) or not frame_bits.endswith(self.FLAG_BIT_PATTERN):
            logger.error("deframe_byte_stuffing: erro - flags de início ou fim ausentes")
            return None, "Erro de enquadramento: formato inválido ou flags ausentes."

        frame_bytes = [int(frame_bits[i:i+8], 2) for i in range(0, len(frame_bits), 8)]
        logger.debug(f"deframe_byte_stuffing: convertido em {len(frame_bytes)} bytes")

        payload_with_stuffing = frame_bytes[1:-1]  # Remove as FLAGs
        destuffed_payload = []
        is_escaped = False

        for i, byte in enumerate(payload_with_stuffing):
            if is_escaped:
                # Byte atual é interpretado como literal após ESC
                destuffed_payload.append(byte)
                is_escaped = False
                logger.debug(f"deframe_byte_stuffing: byte {byte:#04x} pós escape no índice {i}")
            elif byte == self.ESC_BYTE:
                is_escaped = True  # Marca que o próximo byte será escapado
                logger.debug(f"deframe_byte_stuffing: byte escape detectado no índice {i}")
            else:
                destuffed_payload.append(byte)

        if is_escaped:
            logger.error("deframe_byte_stuffing: erro - byte de escape no final do quadro")
            return None, "Erro de enquadramento: byte de escape no final do quadro."

        payload_destuffed_bits = "".join(format(byte, '08b') for byte in destuffed_payload)
        logger.debug(f"deframe_byte_stuffing: saída payload destuffed len={len(payload_destuffed_bits)} bits")
        return payload_destuffed_bits, "OK"

    def frame_bit_stuffing(self, payload_bits):
        """
        Enquadra os dados usando bit stuffing:
        - Insere um '0' após toda sequência de cinco '1's consecutivos.
        - Adiciona FLAGS no início e fim do quadro como delimitadores.
        """
        logger.debug(f"frame_bit_stuffing: entrada payload_bits len={len(payload_bits)}")
        stuffed_payload = payload_bits.replace('11111', '111110')  # Regra de inserção do bit extra
        frame = self.FLAG_BIT_PATTERN + stuffed_payload + self.FLAG_BIT_PATTERN
        logger.debug(f"frame_bit_stuffing: saída frame len={len(frame)}")
        return frame

    def deframe_bit_stuffing(self, frame_bits):
        """
        Remove o enquadramento feito por bit stuffing:
        - Verifica se as flags de início e fim estão presentes.
        - Remove o '0' que foi inserido após cinco '1's consecutivos no payload.
        """
        logger.debug(f"deframe_bit_stuffing: entrada frame_bits len={len(frame_bits)}")
        if not frame_bits.startswith(self.FLAG_BIT_PATTERN) or not frame_bits.endswith(self.FLAG_BIT_PATTERN):
            logger.error("deframe_bit_stuffing: erro - flags de início ou fim não encontradas")
            return None, "Erro de enquadramento: Flag de início ou fim não encontrada."

        stuffed_payload = frame_bits[len(self.FLAG_BIT_PATTERN):-len(self.FLAG_BIT_PATTERN)]
        destuffed_payload = stuffed_payload.replace('111110', '11111')
        logger.debug(f"deframe_bit_stuffing: saída payload len={len(destuffed_payload)}")
        return destuffed_payload, "OK"
