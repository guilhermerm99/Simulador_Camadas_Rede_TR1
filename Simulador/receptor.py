# Simulador/receptor.py

import socket
import sys
import numpy as np
import time
import logging
import time as time_module

# Configurações para reduzir mensagens de debug excessivas de bibliotecas comuns.
logging.getLogger('matplotlib.font_manager').setLevel(logging.WARNING)
logging.getLogger('PIL.PngImagePlugin').setLevel(logging.WARNING)

# Inclui o diretório pai para permitir importações relativas dos módulos locais.
sys.path.append('../')

# Importação dos módulos essenciais para as camadas da simulação:
# - utils: funções auxiliares para conversão de dados.
# - detecção e correção de erros.
# - enquadramento (deframe).
# - demodulação da camada física (modulações de portadora).
from Utilidades import utils
from CamadaEnlace.deteccao_erros import ErrorDetector
from CamadaEnlace.correcao_erros import ErrorCorrector
from CamadaEnlace.enquadramento import Framer
from CamadaFisica.modulacoes_portadora import CarrierModulator

# Configurações padrão da rede e parâmetros do canal de ruído para simulação.
HOST = '127.0.0.1'          # IP local para comunicação via socket TCP.
PORT = 65432                # Porta TCP para escutar conexões.
FATOR_AMPLIFICACAO_RUIDO = 150.0  # Amplificação do ruído para simular erros no canal.

# Configuração do logger para registrar eventos no console e arquivo.
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
    """
    Formata strings longas para logs, limitando o comprimento e indicando truncamento com reticências.
    
    Args:
        data_str (str): String original para formatação.
        max_len (int): Comprimento máximo desejado.
        
    Returns:
        str: String formatada para exibição em logs.
    """
    if len(data_str) > max_len:
        return f"{data_str[:(max_len-3)//2]}...{data_str[-(max_len-3)//2:]}"
    return data_str

def run_receiver(update_callback):
    """
    Função principal que inicia o servidor TCP para receber sinais modulados,
    processa o fluxo da recepção ao desenquadramento, correção e detecção de erros,
    e atualiza a interface gráfica via callbacks com os dados e estados do processo.
    
    Args:
        update_callback (function): Função para atualizar interface gráfica com eventos e dados.
    """
    logger.info(f"Iniciando servidor TCP em {HOST}:{PORT}")
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)     # Cria socket TCP/IP.
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)   # Permite reutilizar o endereço.
    server_socket.bind((HOST, PORT))                                     # Associa socket ao IP e porta.
    server_socket.listen()                                                # Escuta conexões.
    logger.info("Servidor iniciado e escutando conexões.")

    update_callback({'type': 'connection_status', 'message': f"--- SERVIDOR INICIADO ---\nEscutando em {HOST}:{PORT}...", 'color': 'blue'})

    while True:
        logger.info("Aguardando nova conexão...")
        conn, addr = server_socket.accept()   # Aceita nova conexão TCP.
        logger.info(f"Nova conexão aceita de {addr}")
        update_callback({'type': 'new_connection', 'address': str(addr)})

        try:
            with conn:
                start_time = time_module.time()  # Marca o início do processamento da recepção.

                # Recebe metadados da transmissão como string UTF-8.
                metadata_str = conn.recv(1024).decode('utf-8')
                if not metadata_str:
                    logger.warning("Metadados vazios recebidos, ignorando conexão.")
                    continue

                logger.info(f"Metadados recebidos: {metadata_str}")
                parts = metadata_str.split('|')
                # Valida quantidade mínima de campos esperados no metadado.
                if len(parts) < 14:
                    raise ValueError(f"Metadados incompletos recebidos: esperado >=14 partes, recebeu {len(parts)}")

                # Extrai configurações e parâmetros da transmissão, convertendo os tipos.
                qam_pad = int(parts[12]) if parts[12].isdigit() else 0
                original_message_len_bits = int(parts[13]) if parts[13].isdigit() else 0

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
                    "original_payload_len": int(parts[11]),
                    "qam_pad": qam_pad,
                    "original_message_len_bits": original_message_len_bits
                }
                logger.debug(f"Configurações extraídas dos metadados: {config}")
                update_callback({'type': 'received_configs', 'data': config})

                # Recebe o sinal modulado enviado pelo transmissor.
                logger.info("Iniciando recepção do sinal modulado (bytes)...")
                signal_bytes = b""
                while True:
                    packet = conn.recv(4096)
                    if not packet:
                        break
                    signal_bytes += packet

                logger.info(f"Sinal recebido: {len(signal_bytes)} bytes")

                # Converte bytes recebidos para array numpy de floats (amostras do sinal).
                received_signal = np.frombuffer(signal_bytes, dtype=np.float32)
                logger.info(f"Sinal convertido para array numpy com {len(received_signal)} amostras float32")

                # Simula ruído no canal se a taxa de erros for maior que zero.
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

                # Atualiza GUI com o gráfico do sinal recebido antes da demodulação.
                update_callback({'type': 'plot', 'tab': 'pre_demod', 'data': {
                    't': np.arange(len(noisy_signal)) / config["sampling_rate"],
                    'signal_real': noisy_signal,
                    'config': config
                }})

                # Instancia o demodulador com os parâmetros da transmissão e realiza a demodulação.
                logger.info("Iniciando demodulação do sinal...")
                modulator = CarrierModulator(config["bit_rate"], config["freq_base"], config["amplitude"], config["sampling_rate"])
                demodulated_bits, digital_signal_rx, t_digital_rx = modulator.demodulate(noisy_signal, config['mod_portadora_type'], config)
                logger.info(f"Demodulação concluída, {len(demodulated_bits)} bits recuperados")

                # Remove padding que pode ter sido adicionado para ajustar múltiplos de símbolos 8-QAM.
                if config["qam_pad"] > 0:
                    demodulated_bits = demodulated_bits[:-config["qam_pad"]]
                    logger.info(f"Bits de padding removidos após demodulação: {config['qam_pad']} bits")

                # Atualiza GUI com o gráfico do sinal digital após demodulação.
                update_callback({'type': 'plot', 'tab': 'post_demod', 'data': {
                    't': t_digital_rx,
                    'signal': digital_signal_rx,
                    'config': config
                }})

                # Desenquadramento dos bits recebidos para recuperar o payload original.
                logger.info(f"Iniciando desenquadramento com método '{config['enquadramento_type']}'")
                framer = Framer()
                enquadramento = config['enquadramento_type']

                if enquadramento == "Contagem de caracteres":
                    payload, _ = framer.deframe_char_count(demodulated_bits)
                elif enquadramento == "Byte Stuffing (Flags)":
                    payload, _ = framer.deframe_byte_stuffing(demodulated_bits)
                else:  # Bit Stuffing (Flags)
                    payload, _ = framer.deframe_bit_stuffing(demodulated_bits)

                if payload is None:
                    raise ValueError("Erro no desenquadramento - payload nulo.")
                logger.info(f"Payload extraído do quadro com {len(payload)} bits")

                # Inicializa objetos para detecção e correção de erros.
                error_detector = ErrorDetector()
                error_corrector = ErrorCorrector()

                # Aplica correção de erros se código Hamming estiver configurado.
                if config["correcao_erro_type"] == "Hamming":
                    logger.info("Iniciando decodificação e correção pelo código Hamming")
                    data_after_correction, _, relatorio_hamming = error_corrector.decode_hamming(payload)
                    logger.info(f"Relatório Hamming: {relatorio_hamming}")
                else:
                    data_after_correction = payload
                    relatorio_hamming = "N/A (correção desativada)"
                    logger.info("Correção de erros desativada")

                # Atualiza GUI com status da correção Hamming.
                update_callback({'type': 'hamming_status', 'message': relatorio_hamming, 'color': 'blue' if 'corrigido' in relatorio_hamming else 'black'})

                # Realiza a detecção de erros com base na técnica configurada.
                tipo_erro = config["detecao_erro_type"]
                logger.info(f"Tipo de detecção de erro configurado: {tipo_erro}")
                detecao_ok = False
                dados_decodificados = ""

                if tipo_erro == "CRC-32":
                    # Validação do CRC-32 nos dados recebidos.
                    if len(data_after_correction) < 32:
                        raise ValueError("Dados corrigidos menores que tamanho do CRC-32 (32 bits)")

                    dados_decodificados = data_after_correction[:-32]
                    crc_recebido = data_after_correction[-32:]
                    crc_gerado = error_detector.generate_crc(dados_decodificados)
                    detecao_ok = (crc_gerado == crc_recebido)

                    logger.info(f"CRC gerado (recalculado): {crc_gerado}")
                    logger.info(f"CRC recebido: {crc_recebido}")
                    logger.info(f"Validação CRC: {'OK' if detecao_ok else 'INVÁLIDO'}")

                    update_callback({'type': 'detection_result', 'data': {
                        'method': 'CRC-32',
                        'status': 'OK' if detecao_ok else 'INVÁLIDO',
                        'calc': int(crc_gerado, 2),
                        'recv': int(crc_recebido, 2),
                    }})

                elif tipo_erro == "Paridade Par":
                    # Validação por paridade par, usando blocos de 8 bits (7 dados + 1 paridade).
                    if len(data_after_correction) % 8 != 0:
                        raise ValueError("Tamanho de dados inválido para verificação de paridade par (esquema 8-bit)")

                    chunks = [data_after_correction[i:i+8] for i in range(0, len(data_after_correction), 8)]
                    erros = sum(1 for c in chunks if not error_detector.check_even_parity(c))
                    dados_decodificados = "".join(c[:-1] for c in chunks)
                    detecao_ok = (erros == 0)

                    logger.info(f"Detecção por paridade par: {erros} erros detectados")
                    update_callback({'type': 'detection_result', 'data': {
                        'method': 'Paridade Par',
                        'status': "OK" if detecao_ok else f"INVÁLIDO ({erros} erros)"
                    }})

                else:
                    # Nenhuma detecção de erro configurada: assume dados válidos.
                    detecao_ok = True
                    dados_decodificados = data_after_correction
                    update_callback({'type': 'detection_result', 'data': {'method': 'Nenhuma', 'status': 'N/A'}})

                # Remove padding extra de bits da mensagem original, se aplicável.
                if detecao_ok and config['original_message_len_bits'] > 0:
                    dados_decodificados = dados_decodificados[:config['original_message_len_bits']]

                # Converte bits decodificados para texto final, ou indica erro caso a detecção tenha falhado.
                mensagem_final = utils.binary_to_text(dados_decodificados) if detecao_ok else "ERRO: DADOS CORROMPIDOS."

                # Compara os bits originais da mensagem com os decodificados para estatísticas de erro.
                ideal_bits = [int(b) for b in utils.text_to_binary(config["message"])]
                corrected_bits = [int(b) for b in dados_decodificados]
                min_len = min(len(ideal_bits), len(corrected_bits))
                num_erros = sum(1 for a, b in zip(ideal_bits[:min_len], corrected_bits[:min_len]) if a != b) + abs(len(ideal_bits) - len(corrected_bits))

                logger.info(f"Diferenças após correção (ideal vs decodificado): {num_erros} bits diferentes")

                # Atualiza GUI com heatmap que visualiza as posições dos erros nos bits.
                update_callback({'type': 'plot', 'tab': 'heatmap_errors', 'data': {
                    'ideal': ideal_bits[:min_len],
                    'corrected': corrected_bits[:min_len],
                    'errors': [int(a != b) for a, b in zip(ideal_bits[:min_len], corrected_bits[:min_len])],
                    't': t_digital_rx[:min_len]
                }})

                total_time = time_module.time() - start_time  # Tempo total gasto no processamento.

                update_callback({'type': 'final_message', 'message': mensagem_final})
                status_msg = 'Processo Concluído!' if 'ERRO' not in mensagem_final else 'Falha na Integridade dos Dados!'
                update_callback({'type': 'decode_status', 'message': status_msg, 'color': 'green' if 'ERRO' not in mensagem_final else 'red'})
                update_callback({'type': 'metrics', 'data': {
                    'bits_erro_corrigidos': relatorio_hamming,
                    'total_erros': num_erros,
                    'tempo_total': total_time,
                }})

                logger.info(f"Mensagem final decodificada: {format_log(mensagem_final, max_len=120)}")

        except Exception as e:
            # Tratamento de exceções para garantir robustez do receptor e informar erros na GUI.
            err_msg = f"Erro crítico no receptor: {e}"
            logger.error(err_msg, exc_info=True)
            update_callback({'type': 'decode_status', 'message': err_msg, 'color': 'red'})
            update_callback({'type': 'final_message', 'message': 'ERRO: A transmissão falhou.'})

        finally:
            # Finalização do ciclo atual, prepara para nova recepção.
            update_callback({'type': 'connection_status', 'message': 'Aguardando próxima transmissão.', 'color': 'blue'})
            logger.info("Aguardando nova transmissão...")
            time.sleep(1)  # Delay para evitar sobrecarga no loop.
