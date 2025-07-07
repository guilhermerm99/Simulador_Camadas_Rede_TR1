# Simulador/transmissor.py

import socket
import sys
import numpy as np
import time
import logging

# Adiciona o diretório pai ao caminho de busca de módulos para permitir importações locais.
# Isso garante que o Python encontre os módulos das subpastas (e.g., CamadaEnlace, Utilidades).
sys.path.append('../')

# Importação dos módulos que representam as camadas e funcionalidades do simulador.
from Utilidades import utils
from CamadaEnlace.deteccao_erros import ErrorDetector
from CamadaEnlace.correcao_erros import ErrorCorrector
from CamadaEnlace.enquadramento import Framer
from CamadaFisica.modulacoes_digitais import DigitalEncoder
from CamadaFisica.modulacoes_portadora import CarrierModulator

# Configurações básicas da conexão TCP para comunicação entre transmissor e receptor.
HOST = '127.0.0.1' # Endereço IP local para comunicação na mesma máquina.
PORT = 65432       # Porta TCP para a comunicação entre o transmissor e o receptor.

# Configuração do logger para registrar informações e depuração.
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def format_log(data_str, max_len=64):
    """
    Formata strings longas para exibição em logs, truncando o meio para facilitar a leitura.
    Útil para visualizar grandes sequências de bits sem poluir o console.
    
    Args:
        data_str (str): A string a ser formatada.
        max_len (int): O comprimento máximo desejado para a string formatada.
    
    Returns:
        str: A string formatada, com reticências no meio se for muito longa.
    """
    if len(data_str) > max_len:
        # Calcula o tamanho das partes inicial e final para o truncamento.
        return f"{data_str[:(max_len-3)//2]}...{data_str[-(max_len-3)//2:]}"
    return data_str

def run_transmitter(params, update_callback):
    """
    Função principal que orquestra o processo de transmissão de uma mensagem.
    Configura os parâmetros, aplica as etapas das camadas de rede (enlace e física),
    e envia o sinal resultante via socket TCP para o receptor.
    
    Args:
        params (dict): Um dicionário contendo todos os parâmetros de configuração da transmissão
                       (mensagem, tipos de modulação, enquadramento, etc.).
        update_callback (function): Uma função de callback para atualizar a interface gráfica
                                    com o progresso, status e gráficos do processo.
    """
    try:
        # Configuração inicial dos parâmetros da transmissão, extraindo do dicionário 'params'.
        # Valores padrão são definidos onde não são fornecidos, garantindo que a simulação possa ocorrer.
        config = {
            "message": params.get("message"),
            "bits_raw_input": params.get("bits_raw_input"), # String de bits pura, se fornecida pela GUI.
            "enquadramento_type": params.get("enquadramento_type"),
            "mod_digital_type": params.get("mod_digital_type"),
            "mod_portadora_type": params.get("mod_portadora_type"),
            "detecao_erro_type": params.get("detecao_erro_type"),
            "correcao_erro_type": params.get("correcao_erro_type"),
            "taxa_erros": params.get("taxa_erros", 0.0),
            "bit_rate": 1000, # Taxa de bits padrão para a simulação (bits por segundo).
            "freq_base": 5000, # Frequência base da portadora padrão (Hz).
            "amplitude": 1.0   # Amplitude padrão do sinal (Volts).
        }
        # A taxa de amostragem é definida como 20 vezes a taxa de bits para garantir boa resolução do sinal.
        config["sampling_rate"] = config["bit_rate"] * 20
        # O número de amostras por bit é derivado da taxa de amostragem e taxa de bits.
        samples_per_bit = config["sampling_rate"] // config["bit_rate"]


        # Instanciação dos objetos que representam as funcionalidades de cada camada.
        error_detector = ErrorDetector()
        error_corrector = ErrorCorrector()
        framer = Framer()
        digital_encoder = DigitalEncoder()
        modulator = CarrierModulator(config["bit_rate"], config["freq_base"], config["amplitude"], config["sampling_rate"])

        # Notifica a GUI sobre o início do processo de transmissão.
        update_callback({'type': 'status', 'message': "--- INÍCIO DA TRANSMISSÃO ---", 'color': 'black'})
        logger.info("--- INÍCIO DA TRANSMISSÃO ---")

        # --- Camada de Aplicação / Apresentação (implícita) ---
        # 1. Conversão da mensagem para bits.
        # Verifica se a entrada é uma string de bits pura (marcada na GUI) ou texto a ser convertido para ASCII.
        if config.get('bits_raw_input') is not None:
            bits = config['bits_raw_input']
            # O comprimento original da mensagem em bits é o próprio comprimento da string de bits pura.
            config['original_message_len_bits'] = len(bits) 
            logger.info(f"1. (App) Mensagem original (binário puro): {format_log(bits)}")
            update_callback({'type': 'log', 'message': f"1. (App) Mensagem original (binário puro): {len(bits)} bits"})
        else:
            # Converte a mensagem de texto para uma string contínua de bits ASCII (8 bits por caractere).
            bits = utils.text_to_binary(config['message'])
            # O comprimento original da mensagem em bits é o comprimento da string binária ASCII.
            config['original_message_len_bits'] = len(bits)
            logger.info(f"1. (App) Mensagem original em bits (ASCII): {format_log(bits)}")
            update_callback({'type': 'log', 'message': f"1. (App) Mensagem original (ASCII): {len(bits)} bits"})
        
        # --- Camada de Enlace ---
        # 2. Adição de Redundância para Detecção de Erros.
        detecao_selecionada = config["detecao_erro_type"]
        payload_com_detecao = bits # O payload inicial para detecção é a string de bits da mensagem.

        if detecao_selecionada == "CRC-32":
            # Gera o código CRC-32 para os bits da mensagem e o anexa ao final do payload.
            # O CRC é um polinômio de verificação cíclica, usado para detectar erros de transmissão.
            crc = error_detector.generate_crc(bits)
            payload_com_detecao = bits + crc
            logger.info(f"2. (Enlace) Adicionado CRC-32. Payload agora com {len(payload_com_detecao)} bits.")
            update_callback({'type': 'log', 'message': f"2. (Enlace) Adicionado CRC-32. Total: {len(payload_com_detecao)} bits."})

        elif detecao_selecionada == "Paridade Par":
            # Adiciona bits de padding ('0's) para que o comprimento da mensagem seja múltiplo de 7 (para esquema 7+1 bits).
            padding_needed = (7 - len(bits) % 7) % 7
            bits_alinhados = bits + '0' * padding_needed 
            
            # Gera bytes de 8 bits, onde cada 7 bits de dados recebem um bit de paridade par.
            bytes_com_paridade = [error_detector.add_even_parity(bits_alinhados[i:i+7]) for i in range(0, len(bits_alinhados), 7)]
            payload_com_detecao = "".join(bytes_com_paridade)
            
            logger.info(f"2. (Enlace) Adicionada Paridade Par (esquema 7+1). Payload agora com {len(payload_com_detecao)} bits.")
            update_callback({'type': 'log', 'message': f"2. (Enlace) Adicionada Paridade Par. Total: {len(payload_com_detecao)} bits."})
        # Se "Nenhum" for selecionado, 'payload_com_detecao' permanece como 'bits' original.

        # 3. Adição de Redundância para Correção de Erros.
        correcao_selecionada = config["correcao_erro_type"]
        if correcao_selecionada == "Hamming":
            # Aplica o código de Hamming ao payload para permitir correção de erros no receptor.
            # O código de Hamming adiciona bits de paridade extras que permitem identificar e corrigir erros em um único bit.
            bits_para_enlace = error_corrector.encode_hamming(payload_com_detecao)
            logger.info(f"3. (Enlace) Aplicado Hamming. Payload agora com {len(bits_para_enlace)} bits.")
            update_callback({'type': 'log', 'message': f"3. (Enlace) Aplicado Hamming. Total: {len(bits_para_enlace)} bits."})
        else:
            # Se "Nenhum" for selecionado, os bits não são alterados por correção de erros.
            bits_para_enlace = payload_com_detecao

        # 4. Enquadramento (Delimitação de Quadros).
        enquadramento_selecionado = config["enquadramento_type"]
        # Aplica o método de enquadramento selecionado para delimitar o início e fim dos quadros.
        # Isso é crucial para que o receptor saiba onde um quadro começa e termina no fluxo de bits.
        if enquadramento_selecionado == "Contagem de caracteres":
            frame = framer.frame_char_count(bits_para_enlace)
        elif enquadramento_selecionado == "Byte Stuffing (Flags)":
            frame = framer.frame_byte_stuffing(bits_para_enlace)
        else:  # Por padrão, se não for um dos anteriores, assume Bit Stuffing (Flags).
            frame = framer.frame_bit_stuffing(bits_para_enlace)
        logger.info(f"4. (Enlace) Enquadramento '{enquadramento_selecionado}' aplicado. Frame agora com {len(frame)} bits.")
        update_callback({'type': 'log', 'message': f"4. (Enlace) Enquadramento aplicado. Frame: {len(frame)} bits."})

        # --- Camada Física ---
        # 5. Padding para 8-QAM (Alinhamento de Símbolos).
        # Adiciona bits de preenchimento para garantir que o número total de bits seja um múltiplo de 3,
        # necessário para a modulação 8-QAM (3 bits por símbolo).
        mod_portadora = config["mod_portadora_type"]
        if mod_portadora == "8-QAM":
            padding_needed = len(frame) % 3
            if padding_needed != 0:
                qam_pad = 3 - padding_needed
                frame += '0' * qam_pad
                logger.info(f"(Pós-Enquadramento) Adicionado {qam_pad} bits de padding para alinhar o frame final com 8-QAM.")
            else:
                qam_pad = 0
            config["qam_pad"] = qam_pad # Guarda a quantidade de padding para o receptor.
        else:
            config["qam_pad"] = 0 # Nenhuma padding QAM necessário para outras modulações.
            
        # Guarda o comprimento do payload após enquadramento (e possível padding QAM), antes da modulação.
        config['original_payload_len'] = len(frame)
        
        # 6. Codificação Digital (Sinalização em Banda Base).
        # Converte a string de bits do 'frame' em um sinal digital (forma de onda em banda base).
        # Este processo mapeia bits para níveis de tensão ou pulsos, como NRZ-Polar, Manchester ou Bipolar.
        # Passa 'samples_per_bit' explicitamente para garantir o número correto de amostras por bit.
        digital_signal_plot = digital_encoder.encode(frame, config["mod_digital_type"], samples_per_bit)
        logger.info("5. (Física) Codificação de linha gerada para visualização.")
        update_callback({'type': 'log', 'message': f"5. (Física) Codificação de linha aplicada: {config['mod_digital_type']}."})

        # Atualiza a GUI com o gráfico do sinal digital codificado.
        update_callback({'type': 'plot_digital', 'data': {
            't': np.arange(len(digital_signal_plot)) / config["sampling_rate"], # Eixo de tempo correto baseado na taxa de amostragem.
            'signal': digital_signal_plot, # O sinal digital gerado.
            'config': config # Configurações para informações de plotagem.
        }})
        
        # 7. Modulação por Portadora (Transmissão em Banda Passante).
        logger.info(f"6. (Física) Preparando para modular com {mod_portadora}.")

        # Aplica a modulação de portadora selecionada para adaptar o sinal ao meio de transmissão.
        # Isso envolve o uso de uma portadora de alta frequência para transportar o sinal em banda base.
        if mod_portadora == "ASK": # Modulação por Shift de Amplitude (Amplitude-Shift Keying).
            # Para ASK, o sinal digital de entrada é mapeado para níveis de amplitude (0 ou 1) que modulam a portadora.
            signal_source = np.array([1.0 if b == '1' else 0.0 for b in frame])
            t_analog, analog_signal, *qam_points = modulator.modulate(signal_source, mod_portadora)
            logger.info("6. (Física) Modulação por portadora aplicada.")
            update_callback({'type': 'log', 'message': f"6. (Física) Modulação de portadora aplicada: {mod_portadora}."})
        elif mod_portadora == "FSK": # Modulação por Shift de Frequência (Frequency-Shift Keying).
            # Para FSK, o sinal digital de entrada é mapeado para diferentes frequências (+1 ou -1) da portadora.
            signal_source = np.array([1.0 if b == '1' else -1.0 for b in frame])
            t_analog, analog_signal, *qam_points = modulator.modulate(signal_source, mod_portadora)
            logger.info("6. (Física) Modulação por portadora aplicada.")
            update_callback({'type': 'log', 'message': f"6. (Física) Modulação de portadora aplicada: {mod_portadora}."})
        elif mod_portadora == "Nenhum": # Caso a modulação por portadora seja "Nenhum"
            # Se não há modulação de portadora, o sinal "analógico" é o próprio sinal digital em banda base.
            # O `signal_source` deve ser a forma de onda digital (digital_signal_plot)
            signal_source_for_analog = digital_signal_plot # Usa o sinal digital diretamente como "analógico".
            t_analog = np.arange(len(signal_source_for_analog)) / config["sampling_rate"]
            analog_signal = signal_source_for_analog
            qam_points = [] # Não há pontos de constelação para este caso.
            logger.info("6. (Física) Modulação por portadora desativada. Sinal analógico é o sinal digital.")
            update_callback({'type': 'log', 'message': f"6. (Física) Modulação de portadora desativada."})
        else:  # Por padrão, se não for ASK, FSK ou Nenhum, assume 8-QAM.
            # Para 8-QAM, o frame de bits é usado diretamente para mapeamento de constelação.
            signal_source = frame 
            t_analog, analog_signal, *qam_points = modulator.modulate(signal_source, mod_portadora)
            logger.info("6. (Física) Modulação por portadora aplicada.")
            update_callback({'type': 'log', 'message': f"6. (Física) Modulação de portadora aplicada: {mod_portadora}."})

        # Atualiza a interface com o gráfico do sinal analógico modulado.
        update_callback({'type': 'plot_analog', 'data': {'t': t_analog, 'signal': analog_signal, 'config': config}})
        # Se houver pontos QAM (apenas para 8-QAM), atualiza o gráfico da constelação.
        if qam_points:
            update_callback({'type': 'plot_constellation', 'data': {'points': qam_points[0]}})
        
        # --- Transmissão Física (Cabo/Meio) ---
        # 8. Envio via Socket TCP.
        # Estabelece uma conexão TCP com o receptor e envia os metadados e o sinal modulado.
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((HOST, PORT)) # Conecta ao servidor receptor.

            # Monta uma string de metadados contendo todas as configurações da transmissão.
            # Estes metadados são essenciais para que o receptor saiba como interpretar o sinal recebido.
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
                f"{config['original_message_len_bits']}" # Comprimento original da mensagem para o receptor.
            )
            
            # Envia os metadados codificados em UTF-8.
            s.sendall(final_metadata_str.encode('utf-8'))
            time.sleep(0.1) # Pequena pausa para garantir que os metadados sejam processados antes do sinal.
            # ADIÇÃO PARA DEBUG: Verifica o tamanho do sinal analógico antes de enviar.
            logger.info(f"DEBUG: Transmissor - Tamanho do analog_signal antes de enviar: {len(analog_signal)} amostras")
            logger.info(f"DEBUG: Transmissor - Total de bytes a enviar: {len(analog_signal.astype(np.float32).tobytes())} bytes")

            # Envia o sinal analógico modulado, convertido para bytes de float32.
            s.sendall(analog_signal.astype(np.float32).tobytes())

            logger.info("7. (Física) Sinal transmitido via socket.")
            # Notifica a GUI sobre a conclusão da transmissão.
            update_callback({'type': 'status', 'message': 'Transmissão concluída!', 'color': 'green'})

    except Exception as e:
        # Em caso de qualquer erro crítico durante o processo, registra o erro e notifica a GUI.
        logger.error(f"Erro crítico no transmissor: {e}", exc_info=True)
        update_callback({'type': 'status', 'message': f"Erro crítico: {e}", 'color': 'red'})