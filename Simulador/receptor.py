# Simulador/receptor.py

import socket
import sys
import numpy as np
import time
import logging
import time as time_module
logging.getLogger('matplotlib.font_manager').setLevel(logging.WARNING)
logging.getLogger('PIL.PngImagePlugin').setLevel(logging.WARNING)
logging.getLogger('matplotlib.font_manager').setLevel(logging.WARNING)
sys.path.append('../')

from Utilidades import utils
from CamadaEnlace.deteccao_erros import ErrorDetector
from CamadaEnlace.correcao_erros import ErrorCorrector
from CamadaEnlace.enquadramento import Framer
from CamadaFisica.modulacoes_portadora import CarrierModulator

HOST = '127.0.0.1'
PORT = 65432
FATOR_AMPLIFICACAO_RUIDO = 10.0

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s %(levelname)s %(message)s',
    handlers=[
        logging.FileHandler("receptor.log", mode='w', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def format_log(data_str, max_len=64):
    if len(data_str) > max_len:
        return f"{data_str[:(max_len-3)//2]}...{data_str[-(max_len-3)//2:]}"
    return data_str

def run_receiver(update_callback):
    logger.info(f"Iniciando servidor TCP em {HOST}:{PORT}")
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((HOST, PORT))
    server_socket.listen()
    logger.info("Servidor iniciado e escutando conexões.")

    update_callback({'type': 'connection_status', 'message': f"--- SERVIDOR INICIADO ---\nEscutando em {HOST}:{PORT}...", 'color': 'blue'})

    while True:
        logger.info("Aguardando nova conexão...")
        conn, addr = server_socket.accept()
        logger.info(f"Nova conexão aceita de {addr}")
        update_callback({'type': 'new_connection', 'address': str(addr)})

        try:
            with conn:
                start_time = time_module.time()

                metadata_str = conn.recv(1024).decode('utf-8')
                if not metadata_str:
                    logger.warning("Metadados vazios recebidos, ignorando conexão.")
                    continue

                logger.info(f"Metadados recebidos: {metadata_str}")
                parts = metadata_str.split('|')
                if len(parts) < 12:
                    raise ValueError("Metadados incompletos recebidos.")

                config = {
                    "message": parts[0],
                    "enquadramento_type": parts[1],
                    "mod_digital_type": parts[2],
                    "mod_portadora_type": parts[3],
                    "detecao_erro_type": parts[4],
                    "correcao_erro_type": parts[5],
                    "taxa_erros": float(parts[6]),
                    "bit_rate": int(parts[7]),
                    "freq_base": int(parts[8]),
                    "amplitude": float(parts[9]),
                    "sampling_rate": int(parts[10]),
                    "original_payload_len": int(parts[11])
                }
                logger.debug(f"Configurações extraídas dos metadados: {config}")
                update_callback({'type': 'received_configs', 'data': config})

                logger.info("Iniciando recepção do sinal modulado (bytes)...")
                signal_bytes = b""
                while True:
                    packet = conn.recv(4096)
                    if not packet:
                        break
                    signal_bytes += packet

                logger.info(f"Sinal recebido: {len(signal_bytes)} bytes")

                received_signal = np.frombuffer(signal_bytes, dtype=np.float32)
                logger.info(f"Sinal convertido para array numpy com {len(received_signal)} amostras float32")

                taxa_erros = config["taxa_erros"]
                if taxa_erros > 0 and len(received_signal) > 0:
                    energia_media = np.mean(received_signal ** 2)
                    sigma_ruido = np.sqrt(taxa_erros * energia_media * FATOR_AMPLIFICACAO_RUIDO)
                    ruido = np.random.normal(0, sigma_ruido, len(received_signal))
                    noisy_signal = received_signal + ruido
                    logger.info(f"Ruído adicionado ao sinal com sigma={sigma_ruido:.6f}")
                else:
                    noisy_signal = received_signal
                    logger.info("Nenhum ruído adicionado ao sinal")

                update_callback({'type': 'plot', 'tab': 'pre_demod', 'data': {
                    't': np.arange(len(noisy_signal)) / config["sampling_rate"],
                    'signal_real': noisy_signal,
                    'config': config
                }})

                logger.info("Iniciando demodulação do sinal...")
                modulator = CarrierModulator(config["bit_rate"], config["freq_base"], config["amplitude"], config["sampling_rate"])
                demodulated_bits, digital_signal_rx, t_digital_rx = modulator.demodulate(noisy_signal, config)
                logger.info(f"Demodulação concluída, {len(demodulated_bits)} bits recuperados")

                update_callback({'type': 'plot', 'tab': 'post_demod', 'data': {
                    't': t_digital_rx,
                    'signal': digital_signal_rx,
                    'config': config
                }})

                logger.info(f"Iniciando desenquadramento com método '{config['enquadramento_type']}'")
                framer = Framer()
                enquadramento = config['enquadramento_type']

                if enquadramento == "Contagem de caracteres":
                    payload, _ = framer.deframe_char_count(demodulated_bits)
                elif enquadramento == "Byte Stuffing (Flags)":
                    payload, _ = framer.deframe_byte_stuffing(demodulated_bits)
                else:
                    payload, _ = framer.deframe_bit_stuffing(demodulated_bits)

                if payload is None:
                    raise ValueError("Erro no desenquadramento - payload nulo.")

                payload = payload[:config['original_payload_len']]
                logger.info(f"Payload extraído com {len(payload)} bits")

                error_detector = ErrorDetector()
                error_corrector = ErrorCorrector()
                dados_para_corrigir = payload
                detecao_ok = True

                tipo_erro = config["detecao_erro_type"]
                logger.info(f"Tipo de detecção de erro configurado: {tipo_erro}")

                if tipo_erro == "CRC-32":
                    if len(payload) < 32:
                        raise ValueError("Payload menor que tamanho CRC-32")
                    dados_para_corrigir = payload[:-32]
                elif tipo_erro == "Paridade Par":
                    if len(payload) % 9 != 0:
                        raise ValueError("Tamanho inválido para paridade par")
                    chunks = [payload[i:i+9] for i in range(0, len(payload), 9)]
                    erros = sum(1 for c in chunks if not error_detector.check_even_parity(c))
                    dados_para_corrigir = "".join(c[:-1] for c in chunks)
                    detecao_ok = (erros == 0)
                    logger.info(f"Detecção por paridade par: {erros} erros detectados")

                if config["correcao_erro_type"] == "Hamming":
                    logger.info("Iniciando decodificação e correção pelo código Hamming")
                    dados_decodificados, quadro_corrigido, relatorio_hamming = error_corrector.decode_hamming(dados_para_corrigir)
                    logger.info(f"Relatório Hamming: {relatorio_hamming}")
                else:
                    dados_decodificados = quadro_corrigido = dados_para_corrigir
                    relatorio_hamming = "N/A (correção desativada)"
                    logger.info("Correção de erros desativada")

                update_callback({'type': 'hamming_status', 'message': relatorio_hamming, 'color': 'blue' if 'corrigido' in relatorio_hamming else 'black'})

                ideal_bits = [int(b) for b in utils.text_to_binary(config["message"])]
                corrected_bits = [int(b) for b in dados_decodificados]
                min_len = min(len(ideal_bits), len(corrected_bits))
                num_erros = sum(1 for a, b in zip(ideal_bits[:min_len], corrected_bits[:min_len]) if a != b)

                update_callback({'type': 'plot', 'tab': 'heatmap_errors', 'data': {
                    'ideal': ideal_bits[:min_len],
                    'corrected': corrected_bits[:min_len],
                    'errors': [int(a != b) for a, b in zip(ideal_bits[:min_len], corrected_bits[:min_len])],
                    't': t_digital_rx[:min_len]
                }})

                logger.info(f"Diferenças após correção (ideal vs corrigido): {num_erros} bits diferentes")

                update_callback({'type': 'plot', 'tab': 'error_corrected', 'data': {
                    'ideal_bits': ideal_bits[:min_len],
                    'corrected_bits': corrected_bits[:min_len],
                    't_ideal': t_digital_rx[:min_len]
                }})

                update_callback({'type': 'plot', 'tab': 'error', 'data': {
                    'ideal_bits': ideal_bits[:min_len],
                    'received_bits': [int(b) for b in demodulated_bits[:min_len]],
                    't_ideal': t_digital_rx[:min_len]
                }})

                update_callback({'type': 'plot', 'tab': 'corrected_bits', 'data': {
                    't': t_digital_rx[:len(quadro_corrigido)],
                    'signal': [1 if bit == '1' else -1 for bit in quadro_corrigido],
                    'config': config
                }})

                mensagem_final = ""
                decisiva = False
                if tipo_erro == "CRC-32":
                    crc_gerado = error_detector.generate_crc(quadro_corrigido)
                    crc_ok = (crc_gerado == payload[-32:])
                    logger.info(f"CRC gerado: {crc_gerado}")
                    logger.info(f"CRC recebido: {payload[-32:]}")
                    logger.info(f"Validação CRC: {'OK' if crc_ok else 'INVÁLIDO'}")

                    if not error_detector.generate_crc(dados_para_corrigir) == payload[-32:]:
                        decisiva = True

                    update_callback({'type': 'detection_result', 'data': {
                        'method': 'CRC-32',
                        'status': 'OK' if crc_ok else 'INVÁLIDO',
                        'calc': int(crc_gerado, 2),
                        'recv': int(payload[-32:], 2),
                        'correcao_decisiva': decisiva
                    }})

                    mensagem_final = utils.binary_to_text(dados_decodificados) if crc_ok else "ERRO: DADOS CORROMPIDOS."
                elif tipo_erro == "Paridade Par":
                    update_callback({'type': 'detection_result', 'data': {
                        'method': 'Paridade Par',
                        'status': "OK" if detecao_ok else f"INVÁLIDO ({erros} erros)"
                    }})
                    mensagem_final = utils.binary_to_text(dados_decodificados) if detecao_ok else "ERRO: DADOS CORROMPIDOS."
                else:
                    update_callback({'type': 'detection_result', 'data': {'method': 'Nenhuma', 'status': 'N/A'}})
                    mensagem_final = utils.binary_to_text(dados_decodificados)

                total_time = time_module.time() - start_time
                update_callback({'type': 'final_message', 'message': mensagem_final})
                status_msg = 'Processo Concluído!' if 'ERRO' not in mensagem_final else 'Falha na Integridade dos Dados!'
                update_callback({'type': 'decode_status', 'message': status_msg, 'color': 'green' if 'ERRO' not in mensagem_final else 'red'})
                update_callback({'type': 'metrics', 'data': {
                    'bits_erro_corrigidos': relatorio_hamming,
                    'total_erros': num_erros,
                    'tempo_total': total_time,
                    'correcao_decisiva': decisiva
                }})
                logger.info(f"Mensagem final decodificada: {format_log(mensagem_final, max_len=120)}")

        except Exception as e:
            err_msg = f"Erro crítico no receptor: {e}"
            logger.error(err_msg, exc_info=True)
            update_callback({'type': 'decode_status', 'message': err_msg, 'color': 'red'})
            update_callback({'type': 'final_message', 'message': 'ERRO: A transmissão falhou.'})

        finally:
            update_callback({'type': 'connection_status', 'message': 'Aguardando próxima transmissão.', 'color': 'blue'})
            logger.info("Aguardando nova transmissão...")
            time.sleep(1)
