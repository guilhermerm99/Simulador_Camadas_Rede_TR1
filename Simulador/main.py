# Simulador/main.py

import random
import sys
import os

# Ajusta o PYTHONPATH para que os módulos das camadas possam ser importados
# Adiciona o diretório raiz do projeto (Simulador_Camadas_Rede_TR1/) ao PATH
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.append(project_root)

# Importações das camadas
from CamadaFisica import modulacoes_digitais, modulacoes_portadora
from CamadaEnlace import enquadramento, deteccao_erros, correcao_erros

# Importação para Tkinter (se executado diretamente para teste)
import tkinter as tk
from tkinter import ttk, messagebox


class SimuladorRedes:
    def __init__(self):
        print("Simulador de Redes TR1 inicializado.")
        # Mapeamentos para a GUI
        self._enquadramento_options = enquadramento.ENQUADRAMENTO_TX
        self._mod_digital_options = modulacoes_digitais.MODULACOES_DIGITAIS_TX
        self._mod_portadora_options = modulacoes_portadora.MODULACOES_PORTADORA_TX
        self._deteccao_erro_options = deteccao_erros.DETECCAO_ERROS_TX
        self._correcao_erro_options_tx = correcao_erros.CORRECAO_ERROS_TX
        self._correcao_erro_options_rx = correcao_erros.CORRECAO_ERROS_RX
        self._remover_red_correcao_erro_options_rx = correcao_erros.REMOVER_RED_CORRECAO_ERROS_RX


    # Métodos para a GUI acessar as opções de protocolo
    def get_enquadramento_options(self): return self._enquadramento_options
    def get_mod_digital_options(self): return self._mod_digital_options
    def get_mod_portadora_options(self): return self._mod_portadora_options
    def get_deteccao_erro_options(self): return self._deteccao_erro_options
    # A GUI precisa de uma lista de opções para o dropdown
    def get_correcao_erro_options(self): return self._correcao_erro_options_tx


    def simular_transmissao_receptor(self, dados_originais_texto: str, config: dict):
        """
        Orchestrates the data flow from application to physical layer and vice-versa.
        Returns data for the GUI (Tx bits, Rx bits, Rx text, plot data).
        """
        print(f"\n--- INICIANDO SIMULAÇÃO ---")
        print(f"Dados Originais (Aplicação Tx): '{dados_originais_texto}'")

        # --- Transmitter Side (Tx) ---
        print("\n[TRANSMISSOR]")

        # 1. Application Layer (Tx): Bit Encoder
        dados_em_bits_tx = self._simulador_aplicacao_codificador_bits(dados_originais_texto)
        print(f"  Aplicação (bits): {dados_em_bits_tx}")

        # 2. Data Link Layer (Tx)
        # 2.1 Framing
        enquadramento_func = enquadramento.ENQUADRAMENTO_TX[config['tipo_enquadramento']]
        
        # Byte framing needs bytes; others can operate on bits
        if config['tipo_enquadramento'] == 'FLAGS e inserção de bytes':
            # Convert bits to bytes for byte framing
            # Ensure it's a multiple of 8 to convert to bytes
            if len(dados_em_bits_tx) % 8 != 0:
                dados_em_bits_tx_padded = dados_em_bits_tx + '0' * (8 - (len(dados_em_bits_tx) % 8))
            else:
                dados_em_bits_tx_padded = dados_em_bits_tx
            data_bytes = bytes(int(dados_em_bits_tx_padded[i:i+8], 2) for i in range(0, len(dados_em_bits_tx_padded), 8))
            dados_enquadrados = enquadramento_func(data_bytes)
            # Convert back to bit string for next stage (error detection)
            dados_enquadrados_bits = ''.join(format(byte, '08b') for byte in dados_enquadrados)
        else:
            dados_enquadrados_bits = enquadramento_func(dados_em_bits_tx)
        
        print(f"  Enlace (Enquadramento): {dados_enquadrados_bits}")

        # 2.2 Error Correction (Add Hamming bits) - Applied before Error Detection
        # Standard HDLC/IEEE 802.3 usually places CRC last in Tx, and Hamming before.
        # We adjust the order here according to the diagram in the problem statement.
        correcao_erro_tx_func = self._correcao_erro_options_tx[config['tipo_correcao_erro']]
        bits_apos_correcao_tx = correcao_erro_tx_func(dados_enquadrados_bits)
        print(f"  Enlace (Com Correção TX): {bits_apos_correcao_tx}")

        # 2.3 Error Detection (Add CRC/Parity redundancy bits)
        detecao_erro_func = deteccao_erros.DETECCAO_ERROS_TX[config['tipo_detecao_erro']]
        dados_com_redundancia_tx = detecao_erro_func(bits_apos_correcao_tx)
        print(f"  Enlace (Com Detecção TX): {dados_com_redundancia_tx}")
        
        tx_bits_para_fisica = dados_com_redundancia_tx # These are the final bits for the Physical Layer Tx
        print(f"  Enlace (Pronto para Física Tx): {tx_bits_para_fisica}")

        # 3. Physical Layer (Tx): Modulation
        mod_digital_func = modulacoes_digitais.MODULACOES_DIGITAIS_TX[config['tipo_modulacao_digital']]
        sinal_digital_modulado = mod_digital_func(tx_bits_para_fisica)

        mod_portadora_func = modulacoes_portadora.MODULACOES_PORTADORA_TX[config['tipo_modulacao_portadora']]
        sinal_portadora_modulado = mod_portadora_func(tx_bits_para_fisica)
        print(f"  Física (Sinal Portadora Tx): [Sinal Modulado com {len(sinal_portadora_modulado)} amostras]")


        # --- Communication Medium ---
        # Error simulation at the bit level for pipeline simplicity.
        # Ideally, noise would affect the analog signal, and demodulation would decode error-prone bits.
        print("\n[MEIO DE COMUNICAÇÃO]")
        bits_no_meio = self._simular_meio_comunicacao(tx_bits_para_fisica, config['taxa_erros'])
        print(f"  Meio (Bits com erro simulado): {bits_no_meio}")


        # --- Receiver Side (Rx) ---
        print("\n[RECEPTOR]")

        # 4. Physical Layer (Rx): Demodulation (represented by bits from the medium)
        bits_chegando_no_enlace_rx = bits_no_meio
        print(f"  Física (Bits Decodificados): {bits_chegando_no_enlace_rx}")

        # 5. Data Link Layer (Rx)
        # 5.1 Error Detection (Verify redundancy)
        # This verification is done on the COMPLETE frame (with CRC/Parity/Hamming)
        detecao_erro_verificar_func = deteccao_erros.DETECCAO_ERROS_RX[config['tipo_detecao_erro']]
        erro_detectado = not detecao_erro_verificar_func(bits_chegando_no_enlace_rx)
        print(f"  Enlace (Erro Detectado): {erro_detectado}")

        # 5.2 Error Correction (if applicable - Hamming)
        # Hamming acts on the complete frame (with CRC/Parity)
        correcao_erro_rx_func = self._correcao_erro_options_rx[config['tipo_correcao_erro']]
        bits_apos_correcao_rx_completo = correcao_erro_rx_func(bits_chegando_no_enlace_rx)
        print(f"  Enlace (Após Correção Rx): {bits_apos_correcao_rx_completo}")
        
        # Now, remove CRC/Parity AND Hamming bits BEFORE going to the framing layer's deframing.
        # The deframing function should receive only the framed payload.

        # Step A: Remove CRC/Parity from the END of the complete frame.
        final_bits_pre_deframing = bits_apos_correcao_rx_completo
        if config['tipo_detecao_erro'] == 'CRC-32':
            if len(final_bits_pre_deframing) >= deteccao_erros.GRAU_CRC32:
                final_bits_pre_deframing_no_detec_bits = final_bits_pre_deframing[:-deteccao_erros.GRAU_CRC32]
            else:
                final_bits_pre_deframing_no_detec_bits = "" # Error case, insufficient data
                print("  AVISO: Dados insuficientes para remover CRC-32 antes do desenquadramento.")
        elif config['tipo_detecao_erro'] == 'Bit de paridade par':
            if len(final_bits_pre_deframing) >= 1:
                final_bits_pre_deframing_no_detec_bits = final_bits_pre_deframing[:-1]
            else:
                final_bits_pre_deframing_no_detec_bits = "" # Error case, insufficient data
                print("  AVISO: Dados insuficientes para remover Bit de Paridade antes do desenquadramento.")
        else: # No error detection, so no extra bits to remove here
            final_bits_pre_deframing_no_detec_bits = final_bits_pre_deframing

        # Step B: Remove Hamming (if applicable) from the END of the remaining bits.
        # Now, the string "final_bits_pre_deframing_no_detec_bits" contains the bits
        # that were framed + Hamming (if any).
        remover_hamming_func = self._remover_red_correcao_erro_options_rx[config['tipo_correcao_erro']]
        bits_for_deframing_final = remover_hamming_func(final_bits_pre_deframing_no_detec_bits)
        
        # 5.3 Deframing
        desenquadramento_func = enquadramento.ENQUADRAMENTO_RX[config['tipo_enquadramento']]
        
        # The deframing should now operate on bits that ARE JUST THE FRAMED PAYLOAD.
        # The deframing function should return CLEAN data bits.
        if config['tipo_enquadramento'] == 'FLAGS e inserção de bytes':
            # Needs bytes for byte deframing
            if len(bits_for_deframing_final) % 8 != 0:
                padded_bits_final = bits_for_deframing_final + '0' * (8 - (len(bits_for_deframing_final) % 8))
            else:
                padded_bits_final = bits_for_deframing_final
            
            bytes_for_deframing_final = bytes(int(padded_bits_final[i:i+8], 2) for i in range(0, len(padded_bits_final), 8))
            
            dados_desenquadrados_bits_rx = ''.join(format(byte, '08b') for byte in desenquadramento_func(bytes_for_deframing_final))
        else:
            # For 'Contagem de caracteres' and 'FLAGS e inserção de bits',
            # deframing operates on bits and should return only the original data.
            dados_desenquadrados_bits_rx = desenquadramento_func(bits_for_deframing_final)
        
        print(f"  Enlace (Desenquadramento): {dados_desenquadrados_bits_rx}")

        # 6. Application Layer (Rx): Bit to Text Converter
        # At this point, 'dados_desenquadrados_bits_rx' SHOULD BE ONLY THE ORIGINAL DATA BITS.
        dados_recebidos_bits = dados_desenquadrados_bits_rx # No more redundancy to remove here
        
        print(f"  Depuração: Dados Recebidos Bits (antes da conversão p/ texto): {dados_recebidos_bits}")
        dados_recebidos_texto = self._simulador_aplicacao_conversor_bits_para_texto(dados_recebidos_bits)
        print(f"  Aplicação (Texto Rx Final): '{dados_recebidos_texto}'")

        print("\n--- FIM DA SIMULAÇÃO ---")

        return tx_bits_para_fisica, bits_chegando_no_enlace_rx, dados_recebidos_texto, sinal_portadora_modulado


    def _simulador_aplicacao_codificador_bits(self, texto: str) -> str:
        """
        Simulates the Tx Application Layer: Converts text to a bit string (ASCII).
        Simple example, each character becomes 8 bits.
        """
        binary_string = ''.join(format(ord(char), '08b') for char in texto)
        return binary_string

    def _simulador_aplicacao_conversor_bits_para_texto(self, bits: str) -> str:
        """
        Simulates the Rx Application Layer: Converts a bit string to text.
        Handles padding and potential errors to prevent conversion failures.
        """
        text = ''
        if not bits: # Handle empty string immediately
            return ''
            
        # Ensure the bit string is a multiple of 8 for byte processing
        if len(bits) % 8 != 0:
            bits = bits + '0' * (8 - len(bits) % 8)

        for i in range(0, len(bits), 8):
            byte = bits[i:i+8]
            if len(byte) == 8: # Ensure we have a complete byte
                try:
                    char_code = int(byte, 2)
                    # Check if it's a printable ASCII character and common control characters
                    # ASCII: 32 to 126 (printable), 9 (tab), 10 (newline), 13 (carriage return)
                    if (32 <= char_code <= 126) or (char_code in [9, 10, 13]):
                        text += chr(char_code)
                    else:
                        text += '?' # Replace with '?' if it's a non-printable or out-of-range character
                except ValueError:
                    text += '?' # Replace with '?' in case of conversion error
            else:
                pass # Ignore incomplete bits at the end
        return text

    def _simular_meio_comunicacao(self, dados_bits: str, taxa_erros: float) -> str:
        """
        Simulates the communication medium, introducing bit-level errors.
        """
        if not (0.0 <= taxa_erros <= 1.0):
            raise ValueError("Taxa de erros deve estar entre 0.0 e 1.0.")

        sinal_com_erros = list(dados_bits)
        for i in range(len(sinal_com_erros)):
            if random.random() < taxa_erros:
                sinal_com_erros[i] = '1' if sinal_com_erros[i] == '0' else '0' # Invert the bit
        return "".join(sinal_com_erros)


# To run the GUI, execute interface_tkinter.py
if __name__ == "__main__":
    # Start the GUI if this is the main file
    # Note: To run the GUI, execute interface_tkinter.py directly.
    # This block is more for quick console tests.
    root = tk.Tk()
    app = NetworkSimulatorGUI(root)
    root.mainloop()