import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)  # Configure o nível conforme necessidade

class Framer:
    """Gerencia as três técnicas clássicas de enquadramento de dados."""
    
    FLAG_BIT_PATTERN = "01111110"
    FLAG_BYTE = 0x7E
    ESC_BYTE = 0x7D

    def frame_char_count(self, payload_bits):
        logger.debug(f"frame_char_count: entrada payload_bits len={len(payload_bits)}")
        if len(payload_bits) % 8 != 0:
            padding = 8 - (len(payload_bits) % 8)
            payload_bits += '0' * padding
            logger.debug(f"frame_char_count: adicionado padding de {padding} bits")

        num_bytes = len(payload_bits) // 8
        if num_bytes > 255:
            logger.error("frame_char_count: Payload excede o tamanho máximo de 255 bytes")
            raise ValueError("Payload excede o tamanho máximo de 255 bytes.")
        
        header = format(num_bytes, '08b')
        frame = header + payload_bits
        logger.debug(f"frame_char_count: saída frame len={len(frame)}")
        return frame

    def deframe_char_count(self, frame_bits):
        logger.debug(f"deframe_char_count: entrada frame_bits len={len(frame_bits)}")
        header_bits = frame_bits[:8]
        payload_len_in_bytes = int(header_bits, 2)
        payload_len_in_bits = payload_len_in_bytes * 8
        
        payload = frame_bits[8 : 8 + payload_len_in_bits]
        remaining_frame = frame_bits[8 + payload_len_in_bits:]
        logger.debug(f"deframe_char_count: payload len={len(payload)}, restante len={len(remaining_frame)}")
        return payload, remaining_frame

    def frame_byte_stuffing(self, payload_bits):
        logger.debug(f"frame_byte_stuffing: entrada payload_bits len={len(payload_bits)}")
        padding_needed = len(payload_bits) % 8
        if padding_needed != 0:
            num_zeros_to_add = 8 - padding_needed
            payload_bits += '0' * num_zeros_to_add
            logger.debug(f"frame_byte_stuffing: adicionado {num_zeros_to_add} bits de padding para alinhamento em bytes")

        payload_bytes = [int(payload_bits[i:i+8], 2) for i in range(0, len(payload_bits), 8)]
        logger.debug(f"frame_byte_stuffing: convertido em {len(payload_bytes)} bytes")

        stuffed_payload = []
        for byte in payload_bytes:
            if byte == self.FLAG_BYTE or byte == self.ESC_BYTE:
                stuffed_payload.append(self.ESC_BYTE)
                logger.debug(f"frame_byte_stuffing: byte {byte:#04x} escapado")
            stuffed_payload.append(byte)
        
        final_frame_bytes = [self.FLAG_BYTE] + stuffed_payload + [self.FLAG_BYTE]
        frame_bits = "".join(format(byte, '08b') for byte in final_frame_bytes)
        logger.debug(f"frame_byte_stuffing: saída frame_bits len={len(frame_bits)}")
        return frame_bits

    def deframe_byte_stuffing(self, frame_bits):
        logger.debug(f"deframe_byte_stuffing: entrada frame_bits len={len(frame_bits)}")

        if len(frame_bits) % 8 != 0:
            logger.error("deframe_byte_stuffing: erro - frame_bits não é múltiplo de 8")
            return None, "Erro de enquadramento: comprimento inválido (não múltiplo de 8)."
        if not frame_bits.startswith(self.FLAG_BIT_PATTERN) or not frame_bits.endswith(self.FLAG_BIT_PATTERN):
            logger.error("deframe_byte_stuffing: erro - flags de início ou fim ausentes")
            return None, "Erro de enquadramento: formato inválido ou flags ausentes."

        frame_bytes = [int(frame_bits[i:i+8], 2) for i in range(0, len(frame_bits), 8)]
        logger.debug(f"deframe_byte_stuffing: convertido em {len(frame_bytes)} bytes")

        payload_with_stuffing = frame_bytes[1:-1]
        destuffed_payload = []
        is_escaped = False

        for i, byte in enumerate(payload_with_stuffing):
            if is_escaped:
                destuffed_payload.append(byte)
                is_escaped = False
                logger.debug(f"deframe_byte_stuffing: byte {byte:#04x} pós escape no índice {i}")
            elif byte == self.ESC_BYTE:
                is_escaped = True
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
        logger.debug(f"frame_bit_stuffing: entrada payload_bits len={len(payload_bits)}")
        stuffed_payload = payload_bits.replace('011111', '0111110')
        frame = self.FLAG_BIT_PATTERN + stuffed_payload + self.FLAG_BIT_PATTERN
        logger.debug(f"frame_bit_stuffing: saída frame len={len(frame)}")
        return frame

    def deframe_bit_stuffing(self, frame_bits):
        logger.debug(f"deframe_bit_stuffing: entrada frame_bits len={len(frame_bits)}")
        if not frame_bits.startswith(self.FLAG_BIT_PATTERN) or not frame_bits.endswith(self.FLAG_BIT_PATTERN):
            logger.error("deframe_bit_stuffing: erro - flags de início ou fim não encontradas")
            return None, "Erro de enquadramento: Flag de início ou fim não encontrada."
        
        stuffed_payload = frame_bits[len(self.FLAG_BIT_PATTERN):-len(self.FLAG_BIT_PATTERN)]
        destuffed_payload = stuffed_payload.replace('0111110', '011111')
        logger.debug(f"deframe_bit_stuffing: saída payload len={len(destuffed_payload)}")
        return destuffed_payload, "OK"
