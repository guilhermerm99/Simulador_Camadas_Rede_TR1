# Simulador/main.py

import random
import sys
import os
import math

# Ajusta o PYTHONPATH para que os módulos das camadas possam ser importados
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.append(project_root)

# Importações das classes de cada camada do projeto
from CamadaFisica.modulacoes_digitais import ModulacoesDigitais, MODULACOES_DIGITAIS_TX, MODULACOES_DIGITAIS_RX
from CamadaFisica.modulacoes_portadora import ModulacoesPortadora, MODULACOES_PORTADORA_TX, MODULACOES_PORTADORA_RX
from CamadaEnlace.enquadramento import Enquadramento, ENQUADRAMENTO_TX, ENQUADRAMENTO_RX
from CamadaEnlace.deteccao_erros import DeteccaoErros, DETECCAO_ERROS_TX, DETECCAO_ERROS_RX
from CamadaEnlace.correcao_erros import CorrecaoErros, CORRECAO_ERROS_TX, CORRECAO_ERROS_RX, REMOVER_RED_CORRECAO_ERROS_RX

# Importações para Tkinter (se executado diretamente para teste) - Comentado pois o main.py é apenas para os testes em console
# import tkinter as tk
# from tkinter import ttk, messagebox


class SimuladorRedes:
    """
    Classe principal que orquestra a simulação completa da transmissão e recepção de dados
    através das camadas de Aplicação, Enlace e Física. Gerencia o fluxo de dados,
    aplica os protocolos selecionados e simula o meio de comunicação com erros.
    """
    def __init__(self):
        """
        Inicializa o Simulador de Redes, carregando os mapeamentos de funções
        dos protocolos de cada camada.
        """
        print("Simulador de Redes TR1 inicializado.")
        
        # Mapeamentos de funções dos protocolos, usados para chamar dinamicamente
        # as funções selecionadas na GUI. Estes mapeamentos são importados diretamente
        # dos módulos das respectivas camadas.
        self._enquadramento_options_tx = ENQUADRAMENTO_TX
        self._enquadramento_options_rx = ENQUADRAMENTO_RX
        self._mod_digital_options_tx = MODULACOES_DIGITAIS_TX
        self._mod_digital_options_rx = MODULACOES_DIGITAIS_RX
        self._mod_portadora_options_tx = MODULACOES_PORTADORA_TX
        self._mod_portadora_options_rx = MODULACOES_PORTADORA_RX
        self._deteccao_erro_options_tx = DETECCAO_ERROS_TX
        self._deteccao_erro_options_rx = DETECCAO_ERROS_RX
        self._correcao_erro_options_tx = CORRECAO_ERROS_TX
        self._correcao_erro_options_rx = CORRECAO_ERROS_RX
        self._remover_red_correcao_erro_options_rx = REMOVER_RED_CORRECAO_ERROS_RX

        # Instâncias das classes das camadas para acessar constantes como GRAU_CRC32
        self.detector_erros_instance = DeteccaoErros()
        self.corretor_erros_instance = CorrecaoErros() 
        self.enquadramento_instance = Enquadramento() 

    # --- Métodos para a GUI acessar as opções de protocolo ---
    def get_enquadramento_options(self) -> dict: return self._enquadramento_options_tx
    def get_mod_digital_options(self) -> dict: return self._mod_digital_options_tx
    def get_mod_portadora_options(self) -> dict: return self._mod_portadora_options_tx
    def get_deteccao_erro_options(self) -> dict: return self._deteccao_erro_options_tx
    def get_correcao_erro_options(self) -> dict: return self._correcao_erro_options_tx

    def simular_transmissao_receptor(self, dados_originais_texto: str, config: dict) -> tuple[str, str, str, list[float]]:
        """
        Orquestra o fluxo de dados do transmissor ao receptor, aplicando as configurações de protocolo.

        Args:
            dados_originais_texto (str): O texto de entrada fornecido pela camada de aplicação (TX).
            config (dict): Um dicionário contendo as configurações da simulação selecionadas pelo usuário:
                           'tipo_enquadramento', 'tipo_modulacao_digital', 'tipo_modulacao_portadora',
                           'tipo_detecao_erro', 'tipo_correcao_erro', 'taxa_erros'.

        Returns:
            tuple[str, str, str, list[float]]:
                - tx_bits_output (str): Bits após todas as etapas de TX da camada de enlace (pronto para a física).
                - rx_bits_output (str): Bits após todas as etapas de RX da camada de enlace (pronto para a aplicação).
                - rx_text_output (str): Texto final decodificado pela camada de aplicação (RX).
                - signal_plot_data (list[float]): Dados do sinal modulado (camada física TX) para plotagem.
        """
        print(f"\n--- INICIANDO SIMULAÇÃO ---")
        print(f"Dados Originais (Aplicação Tx): '{dados_originais_texto}'")

        # --- Lado do Transmissor (TX) ---
        print("\n[TRANSMISSOR]")

        # 1. Camada de Aplicação (TX): Codificador de Bits
        # Converte o texto de entrada em uma sequência binária (string de '0's e '1's).
        dados_em_bits_tx = self._simulador_aplicacao_codificador_bits(dados_originais_texto)
        print(f"  1. Aplicação (bits): {dados_em_bits_tx}")

        # 2. Camada de Enlace (TX)
        # As etapas na camada de enlace são aplicadas sequencialmente.

        # 2.1 Enquadramento
        # Seleciona a função de enquadramento com base na configuração.
        enquadramento_func_tx = self._enquadramento_options_tx[config['tipo_enquadramento']]
        
        # O enquadramento 'FLAGS e inserção de bytes' opera em bytes, então uma conversão é necessária.
        if config['tipo_enquadramento'] == 'FLAGS e inserção de bytes':
            # Garante que a string de bits tenha comprimento múltiplo de 8 para conversão em bytes.
            padding_len = (8 - len(dados_em_bits_tx) % 8) % 8
            dados_em_bits_tx_padded = dados_em_bits_tx + '0' * padding_len
            
            # Converte a string de bits para uma sequência de bytes.
            data_bytes = bytes(int(dados_em_bits_tx_padded[i:i+8], 2) for i in range(0, len(dados_em_bits_tx_padded), 8))
            
            # Aplica o enquadramento de bytes.
            dados_enquadrados = enquadramento_func_tx(data_bytes)
            
            # Converte os bytes enquadrados de volta para uma string de bits para as próximas etapas.
            dados_enquadrados_bits = ''.join(format(byte, '08b') for byte in dados_enquadrados)
        else:
            # Para outros tipos de enquadramento (Contagem de caracteres, FLAGS e inserção de bits),
            # a operação é feita diretamente na string de bits.
            dados_enquadrados_bits = enquadramento_func_tx(dados_em_bits_tx)
            
        print(f"  2.1 Enlace (Enquadramento): {dados_enquadrados_bits}")

        # 2.2 Correção de Erros (Adicionar bits de Hamming) - Aplicado antes da Detecção.
        # Seleciona a função de correção de erros do transmissor.
        correcao_erro_tx_func = self._correcao_erro_options_tx[config['tipo_correcao_erro']]
        bits_apos_correcao_tx = correcao_erro_tx_func(dados_enquadrados_bits)
        print(f"  2.2 Enlace (Com Correção TX - Hamming): {bits_apos_correcao_tx}")

        # 2.3 Detecção de Erros (Adicionar redundância - CRC/Paridade)
        # Seleciona a função de detecção de erros do transmissor.
        detecao_erro_func_tx = self._deteccao_erro_options_tx[config['tipo_detecao_erro']]
        dados_com_redundancia_tx = detecao_erro_func_tx(bits_apos_correcao_tx)
        print(f"  2.3 Enlace (Com Detecção TX - CRC/Paridade): {dados_com_redundancia_tx}")
        
        # A saída final da camada de enlace do transmissor é o que vai para a camada física.
        tx_bits_para_fisica = dados_com_redundancia_tx 
        print(f"  Enlace (Pronto para Física Tx): {tx_bits_para_fisica}")

        # 3. Camada Física (TX): Modulação
        # Transforma a sequência de bits em um sinal analógico (lista de amplitudes).

        # 3.1 Modulação Digital (Banda-Base)
        # Não é diretamente utilizada para o sinal_portadora_modulado, mas pode ser usada para plotar.
        mod_digital_func_tx = self._mod_digital_options_tx[config['tipo_modulacao_digital']]
        sinal_digital_modulado = mod_digital_func_tx(tx_bits_para_fisica) # Sinal digital para referência

        # 3.2 Modulação por Portadora (final da Camada Física TX)
        mod_portadora_func_tx = self._mod_portadora_options_tx[config['tipo_modulacao_portadora']]
        sinal_portadora_modulado = mod_portadora_func_tx(tx_bits_para_fisica)
        # O sinal modulado por portadora é o sinal final que seria transmitido pelo meio.
        print(f"  3. Física (Sinal Portadora Tx): [Sinal Modulado com {len(sinal_portadora_modulado)} amostras]")


        # --- Meio de Comunicação (Simulação de Canal) ---
        # Neste ponto, o sinal "analógico" é transmitido e pode sofrer interferências (erros de bit).
        # Para simplificar, a simulação de erros é feita diretamente nos bits,
        # como se o demodulador já tivesse processado o ruído no sinal analógico.
        print("\n[MEIO DE COMUNICAÇÃO]")
        # Introduce erros na string de bits que representa o sinal digital após modulação.
        bits_no_meio_com_erros = self._simular_meio_comunicacao(tx_bits_para_fisica, config['taxa_erros'])
        print(f"  Bits transmitidos no meio (com erro simulado): {bits_no_meio_com_erros}")


        # --- Lado do Receptor (RX) ---
        print("\n[RECEPTOR]")

        # 4. Camada Física (RX): Demodulação
        # Os bits que chegam da camada física no receptor, potencialmente com erros.
        bits_chegando_no_enlace_rx = bits_no_meio_com_erros
        print(f"  4. Física (Bits Decodificados para Enlace RX): {bits_chegando_no_enlace_rx}")

        # 5. Camada de Enlace (RX)
        # As operações de RX são a ordem INVERSA das operações de TX.

        # 5.1 Detecção de Erros (Verificar redundância - CRC/Paridade)
        # Esta verificação é feita sobre o quadro COMPLETO (dados + Hamming + CRC/Paridade).
        detecao_erro_verificar_func = self._deteccao_erro_options_rx[config['tipo_detecao_erro']]
        # Retorna True se 'OK', False se 'Erro Detectado'.
        # O retorno para 'Nenhuma' detecção de erros é sempre True.
        erro_detectado_status = detecao_erro_verificar_func(bits_chegando_no_enlace_rx)
        print(f"  5.1 Enlace (Status Detecção Erro): {'Nenhum erro detectado' if erro_detectado_status else 'ERRO DETECTADO'}")
        
        # 5.2 Correção de Erros (Aplicar Hamming)
        # A correção de Hamming opera no quadro completo (dados + Hamming + CRC/Paridade),
        # pois ela repara bits em qualquer parte do quadro recebido.
        correcao_erro_rx_func = self._correcao_erro_options_rx[config['tipo_correcao_erro']]
        # O retorno desta função para Hamming é (codeword_corrigido, mensagem_status).
        # Para 'Nenhuma', retorna (codeword, mensagem).
        bits_apos_correcao_rx_completo, correcao_status_msg = correcao_erro_rx_func(bits_chegando_no_enlace_rx)
        print(f"  5.2 Enlace (Após Correção Rx): {bits_apos_correcao_rx_completo} ({correcao_status_msg})")
        
        # --- VERIFICAÇÃO ADICIONAL: CRC após correção de Hamming ---
        # Se Hamming estava ativo e corrigiu, o CRC (se ativo) deveria agora passar.
        if config['tipo_correcao_erro'] == 'Hamming' and config['tipo_detecao_erro'] == 'CRC-32':
            # Verificamos o CRC no frame que acabou de ser (potencialmente) corrigido pelo Hamming.
            crc_check_after_hamming = self._deteccao_erro_options_rx['CRC-32'](bits_apos_correcao_rx_completo)
            print(f"     Enlace (CRC após Hamming): {'OK' if crc_check_after_hamming else 'Ainda com Erro'}")


        # 5.3 REMOÇÃO de Redundância (CRC/Paridade E Hamming)
        # As redundâncias são removidas na ordem INVERSA em que foram adicionadas no TX.
        # OU SEJA: Primeiro o CRC/Paridade, depois o Hamming.

        # Começamos com os bits que saíram da correção (bits_apos_correcao_rx_completo).
        bits_para_remocao = bits_apos_correcao_rx_completo 
        
        # 5.3.1 Remove os bits de Detecção de Erros (CRC ou Paridade) do final do quadro.
        # Estes bits foram os ÚLTIMOS a serem adicionados no TX.
        print(f"  DEBUG: Bits antes de remover detecção: {bits_para_remocao[:50]}... ({len(bits_para_remocao)} bits)") # DEBUG
        if config['tipo_detecao_erro'] == 'CRC-32':
            # Remove os últimos GRAU_CRC32 bits (que são o CRC).
            if len(bits_para_remocao) >= self.detector_erros_instance.GRAU_CRC32:
                bits_sem_redundancia_deteccao = bits_para_remocao[:-self.detector_erros_instance.GRAU_CRC32]
            else:
                print("  AVISO RX: Dados insuficientes para remover CRC-32. Pode haver truncamento.")
                bits_sem_redundancia_deteccao = "" 
        elif config['tipo_detecao_erro'] == 'Bit de paridade par':
            # Remove o último bit (o bit de paridade).
            if len(bits_para_remocao) >= 1:
                bits_sem_redundancia_deteccao = bits_para_remocao[:-1]
            else:
                print("  AVISO RX: Dados insuficientes para remover Bit de Paridade. Pode haver truncamento.")
                bits_sem_redundancia_deteccao = ""
        else: # Se 'Nenhuma' detecção, a string permanece inalterada.
            bits_sem_redundancia_deteccao = bits_para_remocao

        print(f"  5.3.1 Enlace (Após Remover Detecção RX): {bits_sem_redundancia_deteccao[:50]}... ({len(bits_sem_redundancia_deteccao)} bits)") # DEBUG

        # 5.3.2 Remove os bits de Correção de Erros (Hamming)
        # Estes bits foram adicionados ANTES do CRC no TX.
        remover_hamming_func = self._remover_red_correcao_erro_options_rx[config['tipo_correcao_erro']]
        # Este é o payload enquadrado, sem os bits de redundância de correção e detecção.
        bits_para_desenquadramento = remover_hamming_func(bits_sem_redundancia_deteccao)
        print(f"  5.3.2 Enlace (Após Remover Correção RX - Hamming): {bits_para_desenquadramento[:50]}... ({len(bits_para_desenquadramento)} bits)") # DEBUG
        
        # 5.4 Desenquadramento
        # Agora, a função de desenquadramento opera apenas sobre os bits que formam o payload enquadrado.
        enquadramento_func_rx = self._enquadramento_options_rx[config['tipo_enquadramento']]
        
        if config['tipo_enquadramento'] == 'FLAGS e inserção de bytes':
            # Converte a string de bits (que deve ser múltipla de 8) para bytes para o desenquadramento.
            # Garante que seja um múltiplo de 8 para a conversão.
            padding_len_rx = (8 - len(bits_para_desenquadramento) % 8) % 8
            padded_bits_for_deframing = bits_para_desenquadramento + '0' * padding_len_rx
            
            bytes_para_desenquadramento = bytes(int(padded_bits_for_deframing[i:i+8], 2) 
                                                for i in range(0, len(padded_bits_for_deframing), 8))
            
            # Aplica o desenquadramento de bytes e converte o resultado de volta para string de bits.
            dados_desenquadrados_bits_rx = ''.join(format(byte, '08b') for byte in enquadramento_func_rx(bytes_para_desenquadramento))
        else:
            # Para 'Contagem de caracteres' e 'FLAGS e inserção de bits',
            # o desenquadramento opera e retorna strings de bits.
            dados_desenquadrados_bits_rx = enquadramento_func_rx(bits_para_desenquadramento)
        
        print(f"  5.4 Enlace (Desenquadramento): {dados_desenquadrados_bits_rx[:50]}... ({len(dados_desenquadrados_bits_rx)} bits)") # DEBUG

        # 6. Camada de Aplicação (RX): Conversor de Bits para Texto
        # A este ponto, 'dados_desenquadrados_bits_rx' deve conter APENAS os bits de dados originais.
        dados_recebidos_bits_finais = dados_desenquadrados_bits_rx 
        
        print(f"  6. Depuração: Dados Recebidos Bits (antes da conversão para texto): {dados_recebidos_bits_finais}")
        dados_recebidos_texto = self._simulador_aplicacao_conversor_bits_para_texto(dados_recebidos_bits_finais)
        print(f"  Aplicação (Texto Rx Final): '{dados_recebidos_texto}'")

        print("\n--- FIM DA SIMULAÇÃO ---")

        # Retorna os dados para a GUI exibir.
        return tx_bits_para_fisica, dados_desenquadrados_bits_rx, dados_recebidos_texto, sinal_portadora_modulado


    def _simulador_aplicacao_codificador_bits(self, texto: str) -> str:
        """
        Simula a função da Camada de Aplicação (TX): Converte texto em uma string de bits (ASCII).
        Cada caractere é convertido para sua representação ASCII de 8 bits.

        Args:
            texto (str): O texto de entrada a ser codificado.

        Returns:
            str: A string de bits resultante.
        """
        binary_string = ''.join(format(ord(char), '08b') for char in texto)
        return binary_string

    def _simulador_aplicacao_conversor_bits_para_texto(self, bits: str) -> str:
        """
        Simula a função da Camada de Aplicação (RX): Converte uma string de bits para texto.
        Processa a string de bits em blocos de 8 bits (bytes). Lida com padding e
        caracteres não imprimíveis substituindo-os por '?'.

        Args:
            bits (str): A string de bits a ser decodificada.

        Returns:
            str: O texto decodificado.
        """
        text = ''
        if not bits: # Trata string vazia imediatamente
            return ''
            
        # Garante que a string de bits tenha comprimento múltiplo de 8 para processamento por byte.
        # Adiciona '0's como padding se necessário.
        if len(bits) % 8 != 0:
            bits = bits + '0' * (8 - len(bits) % 8)

        for i in range(0, len(bits), 8):
            byte_segment = bits[i:i+8]
            if len(byte_segment) == 8: # Assegura que temos um byte completo para processar
                try:
                    char_code = int(byte_segment, 2)
                    # Verifica se é um caractere ASCII imprimível ou um caractere de controle comum (tab, newline, CR).
                    # Os códigos ASCII imprimíveis vão de 32 (espaço) a 126 (~).
                    if (32 <= char_code <= 126) or (char_code in [9, 10, 13]):
                        text += chr(char_code)
                    else:
                        # Substitui caracteres não imprimíveis ou fora da faixa ASCII por '?'.
                        text += '?' 
                except ValueError:
                    # Em caso de erro na conversão (ex: byte malformado), substitui por '?'.
                    text += '?' 
            else:
                # Ignora bits incompletos no final da string.
                pass 
        return text

    def _simular_meio_comunicacao(self, dados_bits: str, taxa_erros: float) -> str:
        """
        Simula o meio de comunicação, introduzindo erros de bit com uma dada probabilidade.
        Cada bit tem uma chance 'taxa_erros' de ser invertido.

        Args:
            dados_bits (str): A string de bits a ser transmitida pelo meio.
            taxa_erros (float): A probabilidade de um bit ser invertido (entre 0.0 e 1.0).

        Returns:
            str: A string de bits com erros simulados.

        Raises:
            ValueError: Se a taxa de erros estiver fora do intervalo permitido.
        """
        if not (0.0 <= taxa_erros <= 1.0):
            raise ValueError("Taxa de erros deve estar entre 0.0 e 1.0.")

        sinal_com_erros = list(dados_bits) 
        erros_introduzidos = [] 
        
        # SÓ INTRODUZ ERROS SE A TAXA FOR MAIOR QUE ZERO.
        if taxa_erros > 0.0: 
            for i in range(len(sinal_com_erros)):
                if random.random() < taxa_erros:
                    original_bit = sinal_com_erros[i]
                    sinal_com_erros[i] = '1' if original_bit == '0' else '0'
                    erros_introduzidos.append(f"Pos {i+1} (bit '{original_bit}' -> '{sinal_com_erros[i]}')")
        
        if erros_introduzidos:
            print(f"  Erros introduzidos no meio: {', '.join(erros_introduzidos)}")
        else:
            print("  Nenhum erro introduzido no meio.")

        return "".join(sinal_com_erros)


# Bloco principal para execução dos testes.
if __name__ == "__main__":
    print("Executando Simulador/main.py diretamente para testes de console.")
    simulador_teste = SimuladorRedes()

    # --- INÍCIO DOS TESTES ---

    # --- Grupo de Testes 1: Testes de Funcionalidade Básica (Canal sem Erros) ---

    # Teste 1.1: Enquadramento - Contagem de Caracteres (Sem Erros)
    print("\n--- TESTE 1.1: Enquadramento - Contagem de Caracteres (Sem Erros) ---")
    test_config_1_1 = {
        'tipo_enquadramento': 'Contagem de caracteres',
        'tipo_modulacao_digital': 'NRZ-Polar',
        'tipo_modulacao_portadora': 'ASK',
        'tipo_detecao_erro': 'Nenhuma',
        'tipo_correcao_erro': 'Nenhuma',
        'taxa_erros': 0.0
    }
    input_text_1_1 = "Texto para testar contagem de caracteres"
    tx_bits_out_1_1, rx_bits_out_1_1, rx_text_out_1_1, signal_data_1_1 = \
        simulador_teste.simular_transmissao_receptor(input_text_1_1, test_config_1_1)
    print(f"\nResultado Final do Teste 1.1 (recebido): '{rx_text_out_1_1}'")
    print(f"Resultado Final do Teste 1.1 (esperado): '{input_text_1_1}'")
    print("-" * 80)

    # Teste 1.2: Enquadramento - FLAGS e Inserção de Bytes (Sem Erros, Sem Stuffing Forçado)
    print("\n--- TESTE 1.2: Enquadramento - FLAGS e Inserção de Bytes (Sem Stuffing Forçado, Sem Erros) ---")
    test_config_1_2 = {
        'tipo_enquadramento': 'FLAGS e inserção de bytes',
        'tipo_modulacao_digital': 'NRZ-Polar',
        'tipo_modulacao_portadora': 'ASK',
        'tipo_detecao_erro': 'Nenhuma',
        'tipo_correcao_erro': 'Nenhuma',
        'taxa_erros': 0.0
    }
    input_text_1_2 = "Hello World"
    tx_bits_out_1_2, rx_bits_out_1_2, rx_text_out_1_2, signal_data_1_2 = \
        simulador_teste.simular_transmissao_receptor(input_text_1_2, test_config_1_2)
    print(f"\nResultado Final do Teste 1.2 (recebido): '{rx_text_out_1_2}'")
    print(f"Resultado Final do Teste 1.2 (esperado): '{input_text_1_2}'")
    print("-" * 80)

    # Teste 1.3: Enquadramento - FLAGS e Inserção de Bytes (Sem Erros, COM Stuffing Forçado)
    print("\n--- TESTE 1.3: Enquadramento - FLAGS e Inserção de Bytes (COM Stuffing Forçado, Sem Erros) ---")
    test_config_1_3 = {
        'tipo_enquadramento': 'FLAGS e inserção de bytes',
        'tipo_modulacao_digital': 'NRZ-Polar',
        'tipo_modulacao_portadora': 'ASK',
        'tipo_detecao_erro': 'Nenhuma',
        'tipo_correcao_erro': 'Nenhuma',
        'taxa_erros': 0.0
    }
    # Caracteres ASCII: '~' (0x7E, nossa FLAG_BYTE), '\x10' (0x10, nosso ESC_BYTE)
    input_text_1_3 = "Mensagem com ~ e \x10 para teste de escape!"
    tx_bits_out_1_3, rx_bits_out_1_3, rx_text_out_1_3, signal_data_1_3 = \
        simulador_teste.simular_transmissao_receptor(input_text_1_3, test_config_1_3)
    print(f"\nResultado Final do Teste 1.3 (recebido): '{rx_text_out_1_3}'")
    print(f"Resultado Final do Teste 1.3 (esperado): '{input_text_1_3}'")
    print("-" * 80)

    # Teste 1.4: Enquadramento - FLAGS e Inserção de Bits (Sem Erros, COM Stuffing Forçado)
    print("\n--- TESTE 1.4: Enquadramento - FLAGS e Inserção de Bits (COM Stuffing Forçado, Sem Erros) ---")
    test_config_1_4 = {
        'tipo_enquadramento': 'FLAGS e inserção de bits',
        'tipo_modulacao_digital': 'NRZ-Polar',
        'tipo_modulacao_portadora': 'ASK',
        'tipo_detecao_erro': 'Nenhuma',
        'tipo_correcao_erro': 'Nenhuma',
        'taxa_erros': 0.0
    }
    # Caractere ASCII \xFF é '11111111'. Isso forçará o bit stuffing (111110)
    input_text_1_4 = "Bits " + chr(255) + chr(255) + " devem ser stuffed."
    tx_bits_out_1_4, rx_bits_out_1_4, rx_text_out_1_4, signal_data_1_4 = \
        simulador_teste.simular_transmissao_receptor(input_text_1_4, test_config_1_4)
    print(f"\nResultado Final do Teste 1.4 (recebido): '{rx_text_out_1_4}'")
    print(f"Resultado Final do Teste 1.4 (esperado): '{input_text_1_4}'")
    print("-" * 80)

    # Teste 1.5: Detecção de Erros - Bit de Paridade Par (Sem Erros)
    print("\n--- TESTE 1.5: Detecção de Erros - Bit de Paridade Par (Sem Erros) ---")
    test_config_1_5 = {
        'tipo_enquadramento': 'Contagem de caracteres',
        'tipo_modulacao_digital': 'NRZ-Polar',
        'tipo_modulacao_portadora': 'ASK',
        'tipo_detecao_erro': 'Bit de paridade par',
        'tipo_correcao_erro': 'Nenhuma',
        'taxa_erros': 0.0
    }
    input_text_1_5 = "Paridade"
    tx_bits_out_1_5, rx_bits_out_1_5, rx_text_out_1_5, signal_data_1_5 = \
        simulador_teste.simular_transmissao_receptor(input_text_1_5, test_config_1_5)
    print(f"\nResultado Final do Teste 1.5 (recebido): '{rx_text_out_1_5}'")
    print(f"Resultado Final do Teste 1.5 (esperado): '{input_text_1_5}'")
    print("-" * 80)

    # Teste 1.6: Detecção de Erros - CRC-32 (Sem Erros)
    print("\n--- TESTE 1.6: Detecção de Erros - CRC-32 (Sem Erros) ---")
    test_config_1_6 = {
        'tipo_enquadramento': 'Contagem de caracteres',
        'tipo_modulacao_digital': 'NRZ-Polar',
        'tipo_modulacao_portadora': 'ASK',
        'tipo_detecao_erro': 'CRC-32',
        'tipo_correcao_erro': 'Nenhuma',
        'taxa_erros': 0.0
    }
    input_text_1_6 = "CRC Check"
    tx_bits_out_1_6, rx_bits_out_1_6, rx_text_out_1_6, signal_data_1_6 = \
        simulador_teste.simular_transmissao_receptor(input_text_1_6, test_config_1_6)
    print(f"\nResultado Final do Teste 1.6 (recebido): '{rx_text_out_1_6}'")
    print(f"Resultado Final do Teste 1.6 (esperado): '{input_text_1_6}'")
    print("-" * 80)

    # Teste 1.7: Correção de Erros - Hamming (Sem Erros)
    print("\n--- TESTE 1.7: Correção de Erros - Hamming (Sem Erros) ---")
    test_config_1_7 = {
        'tipo_enquadramento': 'Contagem de caracteres',
        'tipo_modulacao_digital': 'NRZ-Polar',
        'tipo_modulacao_portadora': 'ASK',
        'tipo_detecao_erro': 'Nenhuma',
        'tipo_correcao_erro': 'Hamming',
        'taxa_erros': 0.0
    }
    input_text_1_7 = "Hamming"
    tx_bits_out_1_7, rx_bits_out_1_7, rx_text_out_1_7, signal_data_1_7 = \
        simulador_teste.simular_transmissao_receptor(input_text_1_7, test_config_1_7)
    print(f"\nResultado Final do Teste 1.7 (recebido): '{rx_text_out_1_7}'")
    print(f"Resultado Final do Teste 1.7 (esperado): '{input_text_1_7}'")
    print("-" * 80)

    # Teste 1.8: Modulação Digital - NRZ-Polar (Sem Erros) - Já testado extensivamente em outros combos
    # Incluído para completar a lista
    print("\n--- TESTE 1.8: Modulação Digital - NRZ-Polar (Sem Erros) ---")
    test_config_1_8 = {
        'tipo_enquadramento': 'Contagem de caracteres',
        'tipo_modulacao_digital': 'NRZ-Polar',
        'tipo_modulacao_portadora': 'ASK', # Simples para este teste
        'tipo_detecao_erro': 'Nenhuma',
        'tipo_correcao_erro': 'Nenhuma',
        'taxa_erros': 0.0
    }
    input_text_1_8 = "Digital"
    tx_bits_out_1_8, rx_bits_out_1_8, rx_text_out_1_8, signal_data_1_8 = \
        simulador_teste.simular_transmissao_receptor(input_text_1_8, test_config_1_8)
    print(f"\nResultado Final do Teste 1.8 (recebido): '{rx_text_out_1_8}'")
    print(f"Resultado Final do Teste 1.8 (esperado): '{input_text_1_8}'")
    print("-" * 80)

    # Teste 1.9: Modulação Digital - Manchester (Sem Erros)
    print("\n--- TESTE 1.9: Modulação Digital - Manchester (Sem Erros) ---")
    test_config_1_9 = {
        'tipo_enquadramento': 'Contagem de caracteres',
        'tipo_modulacao_digital': 'Manchester',
        'tipo_modulacao_portadora': 'ASK', # Simples para este teste
        'tipo_detecao_erro': 'Nenhuma',
        'tipo_correcao_erro': 'Nenhuma',
        'taxa_erros': 0.0
    }
    input_text_1_9 = "Manch"
    tx_bits_out_1_9, rx_bits_out_1_9, rx_text_out_1_9, signal_data_1_9 = \
        simulador_teste.simular_transmissao_receptor(input_text_1_9, test_config_1_9)
    print(f"\nResultado Final do Teste 1.9 (recebido): '{rx_text_out_1_9}'")
    print(f"Resultado Final do Teste 1.9 (esperado): '{input_text_1_9}'")
    print("-" * 80)

    # Teste 1.10: Modulação Digital - Bipolar (Sem Erros)
    print("\n--- TESTE 1.10: Modulação Digital - Bipolar (Sem Erros) ---")
    test_config_1_10 = {
        'tipo_enquadramento': 'Contagem de caracteres',
        'tipo_modulacao_digital': 'Bipolar',
        'tipo_modulacao_portadora': 'ASK', # Simples para este teste
        'tipo_detecao_erro': 'Nenhuma',
        'tipo_correcao_erro': 'Nenhuma',
        'taxa_erros': 0.0
    }
    input_text_1_10 = "Bipolar"
    tx_bits_out_1_10, rx_bits_out_1_10, rx_text_out_1_10, signal_data_1_10 = \
        simulador_teste.simular_transmissao_receptor(input_text_1_10, test_config_1_10)
    print(f"\nResultado Final do Teste 1.10 (recebido): '{rx_text_out_1_10}'")
    print(f"Resultado Final do Teste 1.10 (esperado): '{input_text_1_10}'")
    print("-" * 80)

    # Teste 1.11: Modulação por Portadora - ASK (Sem Erros) - Já testado extensivamente em outros combos
    # Incluído para completar a lista
    print("\n--- TESTE 1.11: Modulação por Portadora - ASK (Sem Erros) ---")
    test_config_1_11 = {
        'tipo_enquadramento': 'Contagem de caracteres',
        'tipo_modulacao_digital': 'NRZ-Polar',
        'tipo_modulacao_portadora': 'ASK',
        'tipo_detecao_erro': 'Nenhuma',
        'tipo_correcao_erro': 'Nenhuma',
        'taxa_erros': 0.0
    }
    input_text_1_11 = "ASK"
    tx_bits_out_1_11, rx_bits_out_1_11, rx_text_out_1_11, signal_data_1_11 = \
        simulador_teste.simular_transmissao_receptor(input_text_1_11, test_config_1_11)
    print(f"\nResultado Final do Teste 1.11 (recebido): '{rx_text_out_1_11}'")
    print(f"Resultado Final do Teste 1.11 (esperado): '{input_text_1_11}'")
    print("-" * 80)

    # Teste 1.12: Modulação por Portadora - FSK (Sem Erros)
    print("\n--- TESTE 1.12: Modulação por Portadora - FSK (Sem Erros) ---")
    test_config_1_12 = {
        'tipo_enquadramento': 'Contagem de caracteres',
        'tipo_modulacao_digital': 'NRZ-Polar',
        'tipo_modulacao_portadora': 'FSK',
        'tipo_detecao_erro': 'Nenhuma',
        'tipo_correcao_erro': 'Nenhuma',
        'taxa_erros': 0.0
    }
    input_text_1_12 = "FSK"
    tx_bits_out_1_12, rx_bits_out_1_12, rx_text_out_1_12, signal_data_1_12 = \
        simulador_teste.simular_transmissao_receptor(input_text_1_12, test_config_1_12)
    print(f"\nResultado Final do Teste 1.12 (recebido): '{rx_text_out_1_12}'")
    print(f"Resultado Final do Teste 1.12 (esperado): '{input_text_1_12}'")
    print("-" * 80)

    # Teste 1.13: Modulação por Portadora - 8-QAM (Sem Erros)
    print("\n--- TESTE 1.13: Modulação por Portadora - 8-QAM (Sem Erros) ---")
    test_config_1_13 = {
        'tipo_enquadramento': 'Contagem de caracteres',
        'tipo_modulacao_digital': 'NRZ-Polar',
        'tipo_modulacao_portadora': '8-QAM',
        'tipo_detecao_erro': 'Nenhuma',
        'tipo_correcao_erro': 'Nenhuma',
        'taxa_erros': 0.0
    }
    input_text_1_13 = "QAM"
    tx_bits_out_1_13, rx_bits_out_1_13, rx_text_out_1_13, signal_data_1_13 = \
        simulador_teste.simular_transmissao_receptor(input_text_1_13, test_config_1_13)
    print(f"\nResultado Final do Teste 1.13 (recebido): '{rx_text_out_1_13}'")
    print(f"Resultado Final do Teste 1.13 (esperado): '{input_text_1_13}'")
    print("-" * 80)

    # --- Grupo de Testes 2: Testes de Integração (Canal sem Erros) ---

    # Teste 2.1: Enquadramento por Contagem + CRC-32 + Hamming + NRZ-Polar + ASK (Sem Erros)
    print("\n--- TESTE 2.1: Integração - Completo (Sem Erros) ---")
    test_config_2_1 = {
        'tipo_enquadramento': 'Contagem de caracteres',
        'tipo_modulacao_digital': 'NRZ-Polar',
        'tipo_modulacao_portadora': 'ASK',
        'tipo_detecao_erro': 'CRC-32',
        'tipo_correcao_erro': 'Hamming',
        'taxa_erros': 0.0
    }
    input_text_2_1 = "FullPipelineTest"
    tx_bits_out_2_1, rx_bits_out_2_1, rx_text_out_2_1, signal_data_2_1 = \
        simulador_teste.simular_transmissao_receptor(input_text_2_1, test_config_2_1)
    print(f"\nResultado Final do Teste 2.1 (recebido): '{rx_text_out_2_1}'")
    print(f"Resultado Final do Teste 2.1 (esperado): '{input_text_2_1}'")
    print("-" * 80)

    # Teste 2.2: Enquadramento por Bit Stuffing + CRC-32 + Hamming + Manchester + FSK (Sem Erros)
    print("\n--- TESTE 2.2: Integração - Complexa (Sem Erros) ---")
    test_config_2_2 = {
        'tipo_enquadramento': 'FLAGS e inserção de bits',
        'tipo_modulacao_digital': 'Manchester',
        'tipo_modulacao_portadora': 'FSK',
        'tipo_detecao_erro': 'CRC-32',
        'tipo_correcao_erro': 'Hamming',
        'taxa_erros': 0.0
    }
    # Caractere ASCII \xF8 é '11111000', que forçará bit stuffing.
    # '~' é 01111110, que é a FLAG_BIT_STR, então também testará o comportamento com a FLAG.
    input_text_2_2 = "Complex" + chr(248) + "~Test" 
    tx_bits_out_2_2, rx_bits_out_2_2, rx_text_out_2_2, signal_data_2_2 = \
        simulador_teste.simular_transmissao_receptor(input_text_2_2, test_config_2_2)
    print(f"\nResultado Final do Teste 2.2 (recebido): '{rx_text_out_2_2}'")
    print(f"Resultado Final do Teste 2.2 (esperado): '{input_text_2_2}'")
    print("-" * 80)

    # --- Grupo de Testes 3: Testes com Erros no Canal ---

    # Teste 3.1: Detecção de Erros - Bit de Paridade Par (COM Erro - Um Bit)
    print("\n--- TESTE 3.1: Detecção de Erros - Bit de Paridade Par (COM Erro - Um Bit) ---")
    test_config_3_1 = {
        'tipo_enquadramento': 'Contagem de caracteres',
        'tipo_modulacao_digital': 'NRZ-Polar',
        'tipo_modulacao_portadora': 'ASK',
        'tipo_detecao_erro': 'Bit de paridade par',
        'tipo_correcao_erro': 'Nenhuma',
        'taxa_erros': 0.01 # 1% de chance de erro
    }
    input_text_3_1 = "ErroParidade"
    tx_bits_out_3_1, rx_bits_out_3_1, rx_text_out_3_1, signal_data_3_1 = \
        simulador_teste.simular_transmissao_receptor(input_text_3_1, test_config_3_1)
    print(f"\nResultado Final do Teste 3.1 (recebido): '{rx_text_out_3_1}'")
    print(f"Resultado Final do Teste 3.1 (esperado): '{input_text_3_1}' (Pode haver '?' se erro passar)")
    print("-" * 80)

    # Teste 3.2: Detecção de Erros - CRC-32 (COM Erro)
    print("\n--- TESTE 3.2: Detecção de Erros - CRC-32 (COM Erro) ---")
    test_config_3_2 = {
        'tipo_enquadramento': 'Contagem de caracteres',
        'tipo_modulacao_digital': 'NRZ-Polar',
        'tipo_modulacao_portadora': 'ASK',
        'tipo_detecao_erro': 'CRC-32',
        'tipo_correcao_erro': 'Nenhuma',
        'taxa_erros': 0.05 # 5% de chance de erro
    }
    input_text_3_2 = "ErroCRC"
    tx_bits_out_3_2, rx_bits_out_3_2, rx_text_out_3_2, signal_data_3_2 = \
        simulador_teste.simular_transmissao_receptor(input_text_3_2, test_config_3_2)
    print(f"\nResultado Final do Teste 3.2 (recebido): '{rx_text_out_3_2}'")
    print(f"Resultado Final do Teste 3.2 (esperado): '{input_text_3_2}' (Pode haver '?' se erro passar)")
    print("-" * 80)

    # Teste 3.3: Correção de Erros - Hamming (COM Erro Único - Ideal)
    print("\n--- TESTE 3.3: Correção de Erros - Hamming (COM Erro Único - Ideal) ---")
    test_config_3_3 = {
        'tipo_enquadramento': 'Contagem de caracteres',
        'tipo_modulacao_digital': 'NRZ-Polar',
        'tipo_modulacao_portadora': 'ASK',
        'tipo_detecao_erro': 'CRC-32', # Para verificar se limpa após Hamming
        'tipo_correcao_erro': 'Hamming',
        'taxa_erros': 0.001 # 0.1% de chance de erro (para aumentar chance de 1 erro)
    }
    input_text_3_3 = "HammingCorrige"
    tx_bits_out_3_3, rx_bits_out_3_3, rx_text_out_3_3, signal_data_3_3 = \
        simulador_teste.simular_transmissao_receptor(input_text_3_3, test_config_3_3)
    print(f"\nResultado Final do Teste 3.3 (recebido): '{rx_text_out_3_3}'")
    print(f"Resultado Final do Teste 3.3 (esperado): '{input_text_3_3}' (se Hamming corrigiu com sucesso)")
    print("-" * 80)

    # Teste 3.4: Correção de Erros - Hamming (COM Múltiplos Erros - Forçado)
    print("\n--- TESTE 3.4: Correção de Erros - Hamming (COM Múltiplos Erros - Forçado) ---")
    test_config_3_4 = {
        'tipo_enquadramento': 'Contagem de caracteres',
        'tipo_modulacao_digital': 'NRZ-Polar',
        'tipo_modulacao_portadora': 'ASK',
        'tipo_detecao_erro': 'CRC-32',
        'tipo_correcao_erro': 'Hamming',
        'taxa_erros': 0.1 # 10% de chance de erro (alta para forçar múltiplos)
    }
    input_text_3_4 = "MuitosErros"
    tx_bits_out_3_4, rx_bits_out_3_4, rx_text_out_3_4, signal_data_3_4 = \
        simulador_teste.simular_transmissao_receptor(input_text_3_4, test_config_3_4)
    print(f"\nResultado Final do Teste 3.4 (recebido): '{rx_text_out_3_4}'")
    print(f"Resultado Final do Teste 3.4 (esperado): '{input_text_3_4}' (Pode haver '?' se erros passarem)")
    print("-" * 80)

    # --- Grupo de Testes 4: Casos de Borda e Erros Específicos ---

    # Teste 4.1: Entrada de Texto Vazia
    print("\n--- TESTE 4.1: Entrada de Texto Vazia ---")
    test_config_4_1 = {
        'tipo_enquadramento': 'Contagem de caracteres',
        'tipo_modulacao_digital': 'NRZ-Polar',
        'tipo_modulacao_portadora': 'ASK',
        'tipo_detecao_erro': 'Nenhuma',
        'tipo_correcao_erro': 'Nenhuma',
        'taxa_erros': 0.0
    }
    input_text_4_1 = '' # String vazia
    tx_bits_out_4_1, rx_bits_out_4_1, rx_text_out_4_1, signal_data_4_1 = \
        simulador_teste.simular_transmissao_receptor(input_text_4_1, test_config_4_1)
    print(f"\nResultado Final do Teste 4.1 (recebido): '{rx_text_out_4_1}'")
    print(f"Resultado Final do Teste 4.1 (esperado): '{input_text_4_1}'")
    print("-" * 80)

    # Teste 4.2: Enquadramento por Bit Stuffing com Caractere FLAG nos Dados
    # A FLAG_BIT_STR é '01111110'. Isso deve ser o delimitador.
    # A sequência de stuffing é '11111' -> '111110'.
    # Se a FLAG_BIT_STR aparecer nos dados, ela será stuffed.
    # O caracter '~' em ASCII é 0x7E, que é 01111110. É a FLAG. Será stuffed.
    print("\n--- TESTE 4.2: Enquadramento - Bit Stuffing com Caractere FLAG nos Dados ---")
    test_config_4_2 = {
        'tipo_enquadramento': 'FLAGS e inserção de bits',
        'tipo_modulacao_digital': 'NRZ-Polar',
        'tipo_modulacao_portadora': 'ASK',
        'tipo_detecao_erro': 'Nenhuma',
        'tipo_correcao_erro': 'Nenhuma',
        'taxa_erros': 0.0
    }
    input_text_4_2 = "Dados com a flag ~ e um \xFF (binário 11111111) no meio." 
    tx_bits_out_4_2, rx_bits_out_4_2, rx_text_out_4_2, signal_data_4_2 = \
        simulador_teste.simular_transmissao_receptor(input_text_4_2, test_config_4_2)
    print(f"\nResultado Final do Teste 4.2 (recebido): '{rx_text_out_4_2}'")
    print(f"Resultado Final do Teste 4.2 (esperado): '{input_text_4_2}'")
    print("-" * 80)

    print("\n--- FIM DE TODOS OS TESTES AUTOMATIZADOS ---")