# Simulador/receptor.py

import socket
import sys
import numpy as np
import time
import logging
import time as time_module

# Configurações para reduzir mensagens de depuração excessivas de bibliotecas externas,
# mantendo o console mais limpo e focado nos logs da nossa aplicação.
logging.getLogger('matplotlib.font_manager').setLevel(logging.WARNING)
logging.getLogger('PIL.PngImagePlugin').setLevel(logging.WARNING)

# Adiciona o diretório pai no caminho de busca de módulos do Python.
# Isso é essencial para que possamos importar módulos de outras pastas do projeto (e.g., CamadaEnlace, Utilidades).
sys.path.append('../')

# Importação dos módulos que implementam as funcionalidades de cada camada do nosso simulador.
from Utilidades import utils
from CamadaEnlace.deteccao_erros import ErrorDetector
from CamadaEnlace.correcao_erros import ErrorCorrector
from CamadaEnlace.enquadramento import Framer
from CamadaFisica.modulacoes_portadora import CarrierModulator
from CamadaFisica.modulacoes_digitais import DigitalEncoder 

# Configurações de rede padrão para o servidor do receptor.
HOST = '127.0.0.1'           # Endereço IP local, usado para comunicação entre processos na mesma máquina.
PORT = 65432                 # Porta TCP que o receptor irá escutar por conexões do transmissor.
FATOR_AMPLIFICACAO_RUIDO = 150.0  # Fator usado para ajustar a intensidade do ruído simulado no canal.

# Configuração do sistema de logging para o módulo do receptor.
# Isso nos ajuda a rastrear o fluxo de execução e depurar problemas, registrando eventos no console e em um arquivo.
logging.basicConfig(
    level=logging.DEBUG, # Define o nível mínimo de mensagens a serem registradas (DEBUG, INFO, WARNING, ERROR, CRITICAL).
    format='%(asctime)s %(levelname)s %(message)s', # Formato das mensagens de log (timestamp, nível, mensagem).
    handlers=[
        logging.FileHandler("receptor.log", mode='w', encoding='utf-8'), # Salva os logs em um arquivo, sobrescrevendo a cada execução.
        logging.StreamHandler() # Exibe os logs também no console.
    ]
)
logger = logging.getLogger(__name__) # Obtém uma instância do logger para este módulo.

def format_log(data_str, max_len=64):
    """
    Formata strings longas para exibição concisa em logs.
    Strings que excedem 'max_len' são truncadas no meio com reticências,
    facilitando a leitura de grandes sequências de bits no console.
    
    Args:
        data_str (str): A string original a ser formatada.
        max_len (int): O comprimento máximo desejado para a string formatada.
        
    Returns:
        str: A string formatada, truncada se necessário.
    """
    if len(data_str) > max_len:
        # Calcula o tamanho das partes inicial e final para o truncamento.
        return f"{data_str[:(max_len-3)//2]}...{data_str[-(max_len-3)//2:]}"
    return data_str

def run_receiver(update_callback):
    """
    Função principal que inicializa e gerencia o servidor TCP do receptor.
    Ela aguarda por transmissões, processa o sinal recebido através das camadas
    (física e enlace) e atualiza a interface gráfica com os resultados.
    
    Args:
        update_callback (function): Uma função de callback fornecida pela GUI para
                                    enviar atualizações de status, dados e gráficos.
    """
    logger.info(f"Iniciando servidor TCP em {HOST}:{PORT}")
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)     # Cria um novo socket TCP/IP.
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)   # Permite que o endereço do socket seja reutilizado imediatamente após fechar.
    server_socket.bind((HOST, PORT))                                      # Associa o socket ao endereço IP e porta definidos.
    server_socket.listen()                                                # Coloca o socket em modo de escuta, aguardando por conexões de entrada.
    logger.info("Servidor iniciado e escutando conexões.")

    # Notifica a GUI sobre o status inicial do servidor, informando que está pronto para receber.
    update_callback({'type': 'connection_status', 'message': f"--- SERVIDOR INICIADO ---\nEscutando em {HOST}:{PORT}...", 'color': 'blue'})

    while True: # Loop principal do servidor, que continua a aguardar por novas transmissões.
        logger.info("Aguardando nova conexão...")
        conn, addr = server_socket.accept()   # Aceita uma nova conexão de cliente (transmissor) que se conecta.
        logger.info(f"Nova conexão aceita de {addr}")
        # Notifica a GUI sobre a nova conexão estabelecida.
        update_callback({'type': 'new_connection', 'address': str(addr)})

        try:
            with conn: # Garante que a conexão seja fechada automaticamente após o bloco 'with'.
                start_time = time_module.time()  # Registra o tempo de início do processamento desta transmissão.

                # Camada de Aplicação / Apresentação (implícita) - Recepção de Metadados
                # Recebe as configurações da transmissão do transmissor.
                # Estes metadados são essenciais para o receptor saber como decodificar o sinal.
                metadata_str = conn.recv(1024).decode('utf-8') # Recebe até 1024 bytes de metadados e decodifica.
                if not metadata_str:
                    logger.warning("Metadados vazios recebidos, ignorando conexão.")
                    continue # Pula para a próxima iteração do loop se não houver metadados.

                logger.info(f"Metadados recebidos: {metadata_str}")
                parts = metadata_str.split('|') # Divide a string de metadados em partes usando '|' como delimitador.
                # Valida se todos os campos esperados nos metadados foram recebidos.
                if len(parts) < 14:
                    raise ValueError(f"Metadados incompletos recebidos: esperado >=14 partes, recebeu {len(parts)}")

                # Extrai e converte os parâmetros de configuração dos metadados para os tipos corretos.
                qam_pad = int(parts[12]) if parts[12].isdigit() else 0 # Padding adicionado para alinhar símbolos em 8-QAM.
                original_message_len_bits = int(parts[13]) if parts[13].isdigit() else 0 # Comprimento original da mensagem em bits.

                config = {
                    "message": parts[0], # Mensagem original (texto ou binário puro) enviada.
                    "enquadramento_type": parts[1], # Tipo de enquadramento usado (Camada de Enlace).
                    "mod_digital_type": parts[2], # Tipo de modulação digital (codificação de linha - Camada Física).
                    "mod_portadora_type": parts[3], # Tipo de modulação de portadora (Camada Física).
                    "detecao_erro_type": parts[4], # Tipo de detecção de erro (Camada de Enlace).
                    "correcao_erro_type": parts[5], # Tipo de correção de erro (Camada de Enlace).
                    "taxa_erros": float(parts[6]), # Taxa de erros simulada no canal.
                    "bit_rate": int(parts[7]), # Taxa de bits da transmissão (bps).
                    "freq_base": int(parts[8]), # Frequência base da portadora (Hz).
                    "amplitude": float(parts[9]), # Amplitude do sinal (V).
                    "sampling_rate": int(parts[10]), # Taxa de amostragem do sinal (sps).
                    "original_payload_len": int(parts[11]), # Comprimento do payload antes do padding QAM.
                    "qam_pad": qam_pad, # Quantidade de padding QAM (bits).
                    "original_message_len_bits": original_message_len_bits # Comprimento da mensagem original em bits.
                }
                logger.debug(f"Configurações extraídas dos metadados: {config}")
                # Notifica a GUI com as configurações de transmissão que foram recebidas.
                update_callback({'type': 'received_configs', 'data': config})

                # Camada Física - Recepção do Sinal Modulado
                # Recebe o fluxo de bytes que representa o sinal analógico ou digital modulado.
                logger.info("Iniciando recepção do sinal modulado (bytes)...")
                signal_bytes = b"" # Buffer para armazenar os bytes do sinal.
                while True:
                    packet = conn.recv(4096) # Recebe pacotes de 4096 bytes.
                    if not packet: # Se o pacote estiver vazio, significa que o transmissor terminou de enviar.
                        break
                    signal_bytes += packet # Concatena os bytes recebidos ao buffer.

                logger.info(f"Sinal recebido: {len(signal_bytes)} bytes")

                # Converte os bytes recebidos de volta para um array NumPy de floats (amostras do sinal).
                received_signal = np.frombuffer(signal_bytes, dtype=np.float32)
                logger.info(f"Sinal convertido para array numpy com {len(received_signal)} amostras float32")

                # Camada Física - Simulação de Ruído no Canal
                # Adiciona ruído ao sinal recebido, simulando imperfeições e interferências de um canal real.
                taxa_erros = config["taxa_erros"]
                if taxa_erros > 0 and len(received_signal) > 0:
                    energia_media = np.mean(received_signal ** 2) # Calcula a energia média do sinal para dimensionar o ruído.
                    # Calcula o desvio padrão do ruído com base na taxa de erros desejada e na energia do sinal.
                    sigma_ruido = np.sqrt(taxa_erros * energia_media * FATOR_AMPLIFICACAO_RUIDO) 
                    ruido = np.random.normal(0, sigma_ruido, len(received_signal)) # Gera amostras de ruído gaussiano aleatório.
                    noisy_signal = received_signal + ruido # Adiciona o ruído ao sinal recebido.
                    logger.info(f"Ruído adicionado ao sinal com sigma={sigma_ruido:.6f}")
                else:
                    noisy_signal = received_signal # Se a taxa de erros for zero, o sinal não é alterado.
                    logger.info("Nenhum ruído adicionado ao sinal")

                # Atualiza a GUI com o gráfico do sinal recebido (com ou sem ruído), antes da demodulação.
                # Esta visualização representa o sinal tal como chega à entrada da camada física do receptor.
                update_callback({'type': 'plot', 'tab': 'pre_demod', 'data': {
                    't': np.arange(len(noisy_signal)) / config["sampling_rate"], # Eixo de tempo baseado na taxa de amostragem.
                    'signal_real': noisy_signal, # O sinal recebido (com ruído, se aplicável).
                    'config': config # Configurações para informações de plotagem (e.g., tipo de modulação de portadora).
                }})

                # Camada Física - Demodulação da Portadora
                # Converte o sinal analógico (passa-faixa) de volta para o sinal digital (banda base).
                logger.info("Iniciando demodulação do sinal...")
                # Instancia o DigitalEncoder, que será usado pelo CarrierModulator para reconstruir
                # a forma de onda digital (codificação de linha) após a demodulação da portadora.
                digital_encoder = DigitalEncoder() 
                modulator = CarrierModulator(config["bit_rate"], config["freq_base"], config["amplitude"], config["sampling_rate"])
                
                # Realiza a demodulação da portadora, obtendo os bits recuperados, a forma de onda digital reconstruída e os pontos de constelação (se aplicável).
                demodulated_bits, digital_signal_rx, t_digital_rx, received_qam_points = modulator.demodulate( # ALTERAÇÃO: Adicionado 'received_qam_points'
                    noisy_signal, 
                    config['mod_portadora_type'], 
                    config, 
                    digital_encoder # Passa a instância do digital_encoder para a demodulação.
                )
                logger.info(f"Demodulação concluída, {len(demodulated_bits)} bits recuperados")

                # Remove o padding de bits que pode ter sido adicionado para alinhar símbolos 8-QAM.
                if config["qam_pad"] > 0:
                    demodulated_bits = demodulated_bits[:-config["qam_pad"]]
                    logger.info(f"Bits de padding removidos após demodulação: {config['qam_pad']} bits")

                # Atualiza a GUI com o gráfico do sinal digital reconstruído após a demodulação.
                # Esta visualização representa os bits em banda base, prontos para a camada de enlace.
                update_callback({'type': 'plot', 'tab': 'post_demod', 'data': {
                    't': t_digital_rx, # Eixo de tempo para o sinal digital reconstruído.
                    'signal': digital_signal_rx, # O sinal digital reconstruído (forma de onda da codificação de linha).
                    'config': config # Configurações para informações de plotagem (e.g., tipo de modulação digital).
                }})

                # NOVO: Atualiza a GUI com o gráfico da constelação recebida com ruído, se a modulação for 8-QAM.
                if config['mod_portadora_type'] == '8-QAM' and received_qam_points:
                    update_callback({'type': 'plot', 'tab': 'constellation_rx', 'data': {'points': received_qam_points}})
                    logger.info("Constelação recebida com ruído enviada para plotagem.")


                # Camada de Enlace - Desenquadramento
                # Remove as flags e cabeçalhos do quadro para extrair o payload puro.
                logger.info(f"Iniciando desenquadramento com método '{config['enquadramento_type']}'")
                framer = Framer() # Instancia o objeto Framer para realizar o desenquadramento.
                enquadramento = config['enquadramento_type'] # Obtém o tipo de enquadramento usado pelo transmissor.

                # Aplica o método de desenquadramento correspondente ao tipo configurado.
                if enquadramento == "Contagem de caracteres":
                    payload, _ = framer.deframe_char_count(demodulated_bits)
                elif enquadramento == "Byte Stuffing (Flags)":
                    payload, _ = framer.deframe_byte_stuffing(demodulated_bits)
                else:   # Assume Bit Stuffing (Flags) como padrão se não for um dos anteriores.
                    payload, _ = framer.deframe_bit_stuffing(demodulated_bits)

                if payload is None: # Verifica se o desenquadramento resultou em um payload válido.
                    raise ValueError("Erro no desenquadramento - payload nulo.")
                logger.info(f"Payload extraído do quadro com {len(payload)} bits")

                # Camada de Enlace - Detecção e Correção de Erros
                # Verifica a integridade dos dados e tenta corrigir possíveis erros de transmissão.
                error_detector = ErrorDetector() # Instancia o objeto para detecção de erros.
                error_corrector = ErrorCorrector() # Instancia o objeto para correção de erros.

                # Aplica a correção de erros se o código Hamming estiver configurado.
                if config["correcao_erro_type"] == "Hamming":
                    logger.info("Iniciando decodificação e correção pelo código Hamming")
                    # Tenta decodificar e corrigir erros no payload usando Hamming.
                    data_after_correction, _, relatorio_hamming = error_corrector.decode_hamming(payload)
                    logger.info(f"Relatório Hamming: {relatorio_hamming}")
                else:
                    data_after_correction = payload # Se Hamming não está ativo, os dados não são alterados.
                    relatorio_hamming = "N/A (correção desativada)" # Indica que a correção não foi aplicada.
                    logger.info("Correção de erros desativada")

                # Atualiza a GUI com o status da correção Hamming (erros corrigidos ou não).
                update_callback({'type': 'hamming_status', 'message': relatorio_hamming, 'color': 'blue' if 'corrigido' in relatorio_hamming else 'black'})

                # Realiza a detecção de erros com base na técnica configurada.
                tipo_erro = config["detecao_erro_type"]
                logger.info(f"Tipo de detecção de erro configurado: {tipo_erro}")
                detecao_ok = False # Flag para indicar se a detecção foi bem-sucedida.
                dados_decodificados = "" # String para armazenar os bits após a detecção.

                if tipo_erro == "CRC-32": # Implementação da detecção de erro CRC-32.
                    # Validação do CRC-32: verifica se o comprimento dos dados é suficiente para o CRC.
                    if len(data_after_correction) < 32:
                        raise ValueError("Dados corrigidos menores que tamanho do CRC-32 (32 bits)")

                    dados_decodificados = data_after_correction[:-32] # Remove os 32 bits do CRC do final dos dados.
                    crc_recebido = data_after_correction[-32:] # Extrai o CRC que foi recebido.
                    crc_gerado = error_detector.generate_crc(dados_decodificados) # Recalcula o CRC nos dados recebidos (sem o CRC original).
                    detecao_ok = (crc_gerado == crc_recebido) # Compara os CRCs para determinar a integridade.

                    logger.info(f"CRC gerado (recalculado): {crc_gerado}")
                    logger.info(f"CRC recebido: {crc_recebido}")
                    logger.info(f"Validação CRC: {'OK' if detecao_ok else 'INVÁLIDO'}")

                    # Notifica a GUI com o resultado detalhado da detecção CRC-32.
                    update_callback({'type': 'detection_result', 'data': {
                        'method': 'CRC-32',
                        'status': 'OK' if detecao_ok else 'INVÁLIDO',
                        'calc': int(crc_gerado, 2), # Valor decimal do CRC calculado.
                        'recv': int(crc_recebido, 2), # Valor decimal do CRC recebido.
                    }})

                elif tipo_erro == "Paridade Par": # Implementação da detecção de erro por Paridade Par.
                    # Validação por paridade par: verifica se o comprimento dos dados é múltiplo de 8.
                    if len(data_after_correction) % 8 != 0:
                        raise ValueError("Tamanho de dados inválido para verificação de paridade par (esquema 8-bit)")

                    chunks = [data_after_correction[i:i+8] for i in range(0, len(data_after_correction), 8)] # Divide os dados em blocos de 8 bits.
                    erros = sum(1 for c in chunks if not error_detector.check_even_parity(c)) # Conta quantos blocos têm erro de paridade.
                    dados_decodificados = "".join(c[:-1] for c in chunks) # Remove o bit de paridade de cada bloco para obter os dados originais.
                    detecao_ok = (erros == 0) # A detecção é considerada OK se nenhum erro de paridade foi encontrado.

                    logger.info(f"Detecção por paridade par: {erros} erros detectados")
                    # Notifica a GUI com o resultado da detecção por paridade par.
                    update_callback({'type': 'detection_result', 'data': {
                        'method': 'Paridade Par',
                        'status': "OK" if detecao_ok else f"INVÁLIDO ({erros} erros)"
                    }})

                else: # Caso o tipo de detecção de erro seja "Nenhum".
                    detecao_ok = True # Assume que os dados são válidos, pois nenhuma detecção foi aplicada.
                    dados_decodificados = data_after_correction # Os dados não são alterados.
                    # Notifica a GUI que a detecção de erro está desativada.
                    update_callback({'type': 'detection_result', 'data': {'method': 'Nenhuma', 'status': 'N/A'}})

                # Remove o padding extra de bits que pode ter sido adicionado à mensagem original, se aplicável.
                # Isso garante que a mensagem final tenha o comprimento exato da mensagem original do transmissor.
                if detecao_ok and config['original_message_len_bits'] > 0:
                    dados_decodificados = dados_decodificados[:config['original_message_len_bits']]

                # Camada de Aplicação / Apresentação (implícita) - Conversão Final para Texto
                # Converte os bits decodificados de volta para texto. Se a detecção de erro falhou,
                # uma mensagem de erro é exibida.
                mensagem_final = utils.binary_to_text(dados_decodificados) if detecao_ok else "ERRO: DADOS CORROMPIDOS."

                # Compara os bits da mensagem original (transmitida) com os bits decodificados para calcular a taxa de erro final.
                # Isso ajuda a avaliar a eficácia das técnicas de correção e detecção.
                ideal_bits_str = config["message"] if all(b in '01' for b in config["message"]) else utils.text_to_binary(config["message"])
                
                ideal_bits = [int(b) for b in ideal_bits_str] # Converte a string de bits ideal para uma lista de inteiros.
                corrected_bits = [int(b) for b in dados_decodificados] # Converte os bits decodificados para uma lista de inteiros.
                min_len = min(len(ideal_bits), len(corrected_bits)) # Determina o comprimento mínimo para comparação bit a bit.
                # Calcula o número total de erros, incluindo bits diferentes e diferenças de comprimento.
                num_erros = sum(1 for a, b in zip(ideal_bits[:min_len], corrected_bits[:min_len]) if a != b) + abs(len(ideal_bits) - len(corrected_bits))

                logger.info(f"Diferenças após correção (ideal vs decodificado): {num_erros} bits diferentes")

                total_time = time_module.time() - start_time  # Calcula o tempo total gasto no processamento desta transmissão.

                # Atualiza a GUI com a mensagem final decodificada e o status geral do processo.
                update_callback({'type': 'final_message', 'message': mensagem_final})
                status_msg = 'Processo Concluído!' if 'ERRO' not in mensagem_final else 'Falha na Integridade dos Dados!'
                update_callback({'type': 'decode_status', 'message': status_msg, 'color': 'green' if 'ERRO' not in mensagem_final else 'red'})
                # Atualiza a GUI com as métricas de desempenho (erros corrigidos, total de erros, tempo).
                update_callback({'type': 'metrics', 'data': {
                    'bits_erro_corrigidos': relatorio_hamming, # Relatório detalhado de erros corrigidos por Hamming.
                    'total_erros': num_erros, # Número total de erros detectados após todas as etapas.
                    'tempo_total': total_time, # Tempo total de processamento para esta transmissão.
                }})

                logger.info(f"Mensagem final decodificada: {format_log(mensagem_final, max_len=120)}")

        except Exception as e:
            # Captura e trata qualquer erro crítico que ocorra durante o processamento da recepção.
            err_msg = f"Erro crítico no receptor: {e}"
            logger.error(err_msg, exc_info=True) # Registra o erro completo no log.
            # Notifica a GUI sobre o erro, exibindo uma mensagem de falha.
            update_callback({'type': 'decode_status', 'message': err_msg, 'color': 'red'})
            update_callback({'type': 'final_message', 'message': 'ERRO: A transmissão falhou.'})

        finally:
            # Bloco 'finally' garante que estas ações sejam executadas independentemente de ocorrer um erro ou não.
            # Prepara o receptor para a próxima transmissão, atualizando o status na GUI.
            update_callback({'type': 'connection_status', 'message': 'Aguardando próxima transmissão.', 'color': 'blue'})
            logger.info("Aguardando nova transmissão...")
            time.sleep(1) # Pequeno atraso para evitar sobrecarga do CPU em um loop contínuo.