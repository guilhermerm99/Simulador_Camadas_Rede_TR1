# Simulador/transmissor.py

import socket, sys, numpy as np, time
import logging

sys.path.append('../')
from Utilidades import utils
from CamadaEnlace.deteccao_erros import ErrorDetector
from CamadaEnlace.correcao_erros import ErrorCorrector
from CamadaEnlace.enquadramento import Framer
from CamadaFisica.modulacoes_digitais import DigitalEncoder
from CamadaFisica.modulacoes_portadora import CarrierModulator

HOST = '127.0.0.1'
PORT = 65432

logger = logging.getLogger(__name__)

def format_log(data_str, max_len=64):
    if len(data_str) > max_len:
        return f"{data_str[:(max_len-3)//2]}...{data_str[-(max_len-3)//2:]}"
    return data_str

def run_transmitter(params, update_callback):
    try:
        config = {
            "message": params.get("message"),
            "enquadramento_type": params.get("enquadramento_type"),
            "mod_digital_type": params.get("mod_digital_type"),
            "mod_portadora_type": params.get("mod_portadora_type"),
            "detecao_erro_type": params.get("detecao_erro_type"),
            "correcao_erro_type": params.get("correcao_erro_type"),
            "taxa_erros": params.get("taxa_erros", 0.0),
            "bit_rate": 1000,
            "freq_base": 5000,
            "amplitude": 1.0
        }
        config["sampling_rate"] = config["bit_rate"] * 20

        error_detector = ErrorDetector()
        error_corrector = ErrorCorrector()
        framer = Framer()
        digital_encoder = DigitalEncoder()
        modulator = CarrierModulator(config["bit_rate"], config["freq_base"], config["amplitude"], config["sampling_rate"])

        update_callback({'type': 'status', 'message': "--- INÍCIO DA TRANSMISSÃO ---", 'color': 'black'})
        logger.info("--- INÍCIO DA TRANSMISSÃO ---")

        bits = utils.text_to_binary(config['message'])
        # Armazena o comprimento original da mensagem em bits para remover o padding no receptor
        config['original_message_len_bits'] = len(bits)
        
        logger.info(f"1. (App) Mensagem original em bits: {format_log(bits)}")
        update_callback({'type': 'log', 'message': f"1. (App) Mensagem original: {len(bits)} bits"})

        # Camada de Enlace: Detecção de erro
        detecao_selecionada = config["detecao_erro_type"]
        payload_com_detecao = bits

        if detecao_selecionada == "CRC-32":
            crc = error_detector.generate_crc(bits)
            payload_com_detecao = bits + crc
            logger.info(f"2. (Enlace) Adicionado CRC-32. Payload agora com {len(payload_com_detecao)} bits.")
            update_callback({'type': 'log', 'message': f"2. (Enlace) Adicionado CRC-32. Total: {len(payload_com_detecao)} bits."})
        elif detecao_selecionada == "Paridade Par":
            # CORREÇÃO: Implementa o esquema padrão 7+1 para paridade.
            # Adiciona padding para tornar o comprimento dos bits um múltiplo de 7.
            padding_needed = (7 - len(bits) % 7) % 7
            bits_alinhados = bits + '0' * padding_needed
            
            # Adiciona 1 bit de paridade a cada bloco de 7 bits, formando bytes de 8 bits.
            bytes_com_paridade = [error_detector.add_even_parity(bits_alinhados[i:i+7]) for i in range(0, len(bits_alinhados), 7)]
            payload_com_detecao = "".join(bytes_com_paridade)
            
            logger.info(f"2. (Enlace) Adicionada Paridade Par (esquema 7+1). Payload agora com {len(payload_com_detecao)} bits.")
            update_callback({'type': 'log', 'message': f"2. (Enlace) Adicionada Paridade Par. Total: {len(payload_com_detecao)} bits."})

        # Camada de Enlace: Correção de erro
        correcao_selecionada = config["correcao_erro_type"]
        if correcao_selecionada == "Hamming":
            bits_para_enlace = error_corrector.encode_hamming(payload_com_detecao)
            logger.info(f"3. (Enlace) Aplicado Hamming. Payload agora com {len(bits_para_enlace)} bits.")
            update_callback({'type': 'log', 'message': f"3. (Enlace) Aplicado Hamming. Total: {len(bits_para_enlace)} bits."})
        else:
            bits_para_enlace = payload_com_detecao

        # Camada de Enlace: Enquadramento
        enquadramento_selecionado = config["enquadramento_type"]
        if enquadramento_selecionado == "Contagem de caracteres":
            frame = framer.frame_char_count(bits_para_enlace)
        elif enquadramento_selecionado == "Byte Stuffing (Flags)":
            frame = framer.frame_byte_stuffing(bits_para_enlace)
        else: # Bit Stuffing (Flags)
            frame = framer.frame_bit_stuffing(bits_para_enlace)
        logger.info(f"4. (Enlace) Enquadramento '{enquadramento_selecionado}' aplicado. Frame agora com {len(frame)} bits.")
        update_callback({'type': 'log', 'message': f"4. (Enlace) Enquadramento aplicado. Frame: {len(frame)} bits."})

        # Camada Física: Padding para 8-QAM
        mod_portadora = config["mod_portadora_type"]
        if mod_portadora == "8-QAM":
            padding_needed = len(frame) % 3
            if padding_needed != 0:
                qam_pad = 3 - padding_needed
                frame += '0' * qam_pad
                logger.info(f"(Pós-Enquadramento) Adicionado {qam_pad} bits de padding para alinhar o frame final com 8-QAM.")
            else:
                qam_pad = 0
            config["qam_pad"] = qam_pad
        else:
            config["qam_pad"] = 0
            
        config['original_payload_len'] = len(frame)
        
        # Camada Física: Codificação digital (linha)
        digital_signal_plot = digital_encoder.encode(frame, config["mod_digital_type"])
        update_callback({'type': 'plot_digital', 'data': {
            't': np.arange(len(digital_signal_plot)) * (1.0 / config["bit_rate"]),
            'signal': digital_signal_plot,
            'config': config
        }})
        logger.info("5. (Física) Codificação de linha gerada para visualização.")
        update_callback({'type': 'log', 'message': "5. (Física) Codificação de linha aplicada."})

        # Camada Física: Modulação por portadora
        logger.info(f"6. (Física) Preparando para modular com {mod_portadora}.")

        if mod_portadora == "ASK":
            signal_source = np.array([1.0 if b == '1' else 0.0 for b in frame])
        elif mod_portadora == "FSK":
            signal_source = np.array([1.0 if b == '1' else -1.0 for b in frame])
        else:  # 8-QAM
            signal_source = frame 

        t_analog, analog_signal, *qam_points = modulator.modulate(signal_source, mod_portadora)

        update_callback({'type': 'plot_analog', 'data': {'t': t_analog, 'signal': analog_signal, 'config': config}})
        if qam_points:
            update_callback({'type': 'plot_constellation', 'data': {'points': qam_points[0]}})
        logger.info("6. (Física) Modulação por portadora aplicada.")
        update_callback({'type': 'log', 'message': "6. (Física) Modulação de portadora aplicada."})

        # Transmissão via socket
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((HOST, PORT))

            # Montagem dos metadados para envio, incluindo o comprimento original da mensagem
            final_metadata_str = (
                f"{config['message']}|"
                f"{config['enquadramento_type']}|"
                f"{config['mod_digital_type']}|"
                f"{config['mod_portadora_type']}|"
                f"{config['detecao_erro_type']}|"
                f"{config['correcao_erro_type']}|"
                f"{config['taxa_erros']}|"
                f"{config['bit_rate']}|"
                f"{config['freq_base']}|"
                f"{config['amplitude']}|"
                f"{config['sampling_rate']}|"
                f"{config['original_payload_len']}|"
                f"{config['qam_pad']}|"
                f"{config['original_message_len_bits']}" # Novo campo
            )
            
            s.sendall(final_metadata_str.encode('utf-8'))
            time.sleep(0.1)
            s.sendall(analog_signal.astype(np.float32).tobytes())

            logger.info("7. (Física) Sinal transmitido via socket.")
            update_callback({'type': 'status', 'message': 'Transmissão concluída!', 'color': 'green'})

    except Exception as e:
        logger.error(f"Erro crítico no transmissor: {e}", exc_info=True)
        update_callback({'type': 'status', 'message': f"Erro crítico: {e}", 'color': 'red'})
