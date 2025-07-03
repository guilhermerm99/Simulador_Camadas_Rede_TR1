# CamadaFisica/modulacoes_portadora.py

import numpy as np
import math

class CarrierModulator:
    """Implementa as modulações de portadora (ASK, FSK, 8-QAM)."""

    def __init__(self, bit_rate, carrier_freq, amplitude, sampling_rate):
        self.bit_rate = bit_rate
        self.carrier_freq = carrier_freq
        self.amplitude = amplitude
        self.sampling_rate = sampling_rate
        self.samples_per_bit = int(self.sampling_rate / self.bit_rate)

    def modulate(self, signal_source, modulation_type):
        if modulation_type == "ASK": return self.modulate_ask(signal_source)
        elif modulation_type == "FSK": return self.modulate_fsk(signal_source)
        elif modulation_type == "8-QAM": return self.modulate_8qam(signal_source)
        else: raise ValueError(f"Tipo de modulação desconhecido: {modulation_type}")

    def modulate_ask(self, digital_signal):
        num_bits = len(digital_signal)
        num_total_samples = num_bits * self.samples_per_bit
        total_time = num_bits / self.bit_rate
        t = np.linspace(0, total_time, num_total_samples, endpoint=False)
        
        amplitude_levels = np.zeros_like(digital_signal, dtype=float)
        amplitude_levels[digital_signal == 1] = self.amplitude
        
        amplitude_signal = np.repeat(amplitude_levels, self.samples_per_bit)
        
        min_len = min(len(amplitude_signal), len(t))
        carrier_wave = np.sin(2 * np.pi * self.carrier_freq * t[:min_len])
        modulated_signal = amplitude_signal[:min_len] * carrier_wave
        
        return t[:min_len], modulated_signal

    def modulate_fsk(self, digital_signal):
        num_bits = len(digital_signal)
        num_total_samples = num_bits * self.samples_per_bit
        total_time = num_bits / self.bit_rate
        t = np.linspace(0, total_time, num_total_samples, endpoint=False)
        
        f_dev = self.bit_rate; f1 = self.carrier_freq + f_dev; f2 = self.carrier_freq - f_dev
        
        modulated_signal = np.zeros_like(t)
        for i, level in enumerate(digital_signal):
            start = i * self.samples_per_bit; end = (i + 1) * self.samples_per_bit
            freq = self.carrier_freq
            if level == 1: freq = f1
            elif level == -1: freq = f2
            modulated_signal[start:end] = self.amplitude * np.sin(2 * np.pi * freq * t[start:end])
            
        return t, modulated_signal

    def modulate_8qam(self, bits):
        # ... (esta função não precisa de mudanças) ...
        QAM8_MAP = {'000': complex(-1, 1), '001': complex(-1, 3), '011': complex(1, 3), '010': complex(1, 1), '100': complex(-1, -1), '101': complex(-1, -3), '111': complex(1, -3), '110': complex(1, -1),}
        padding = len(bits) % 3; 
        if padding != 0: bits += '0' * (3 - padding)
        symbols = [bits[i:i+3] for i in range(0, len(bits), 3)]; qam_points = [QAM8_MAP.get(s, complex(0,0)) for s in symbols]
        num_symbols = len(qam_points); samples_per_symbol = self.samples_per_bit * 3; num_total_samples = num_symbols * samples_per_symbol
        total_time = num_symbols / (self.bit_rate / 3.0)
        t = np.linspace(0, total_time, num_total_samples, endpoint=False)
        modulated_signal = np.zeros(num_total_samples)
        for i, point in enumerate(qam_points):
            start = i * samples_per_symbol; end = (i + 1) * samples_per_symbol
            i_comp = point.real * self.amplitude; q_comp = point.imag * self.amplitude
            cos_carrier = np.cos(2 * np.pi * self.carrier_freq * t[start:end]); sin_carrier = np.sin(2 * np.pi * self.carrier_freq * t[start:end])
            modulated_signal[start:end] = i_comp * cos_carrier - q_comp * sin_carrier
        return t, modulated_signal, qam_points

    # <<< INÍCIO DA CORREÇÃO PRINCIPAL >>>
    def demodulate(self, received_signal, config):
        """
        Demodulador coerente para ASK, mais robusto ao ruído.
        """
        bit_rate = config['bit_rate']
        sampling_rate = config['sampling_rate']
        carrier_freq = config['freq_base']
        mod_digital_type = config['mod_digital_type']
        
        samples_per_bit = int(sampling_rate / bit_rate)
        num_bits = len(received_signal) // samples_per_bit
        
        digital_signal = np.zeros(num_bits)
        demodulated_bits = ""

        # Cria um template de tempo para um único bit
        t_bit = np.linspace(0, 1.0/bit_rate, samples_per_bit, endpoint=False)
        # Gera uma portadora local para correlação
        local_carrier = np.sin(2 * np.pi * carrier_freq * t_bit)

        for i in range(num_bits):
            start = i * samples_per_bit
            end = (i + 1) * samples_per_bit
            segment = received_signal[start:end]

            # Garante que o segmento tenha o tamanho correto para a operação
            if len(segment) != len(local_carrier):
                continue # Pula bits incompletos no final do sinal

            # Multiplica o sinal recebido pela portadora local e integra (soma)
            correlation = np.sum(segment * local_carrier)

            # Define um limiar de decisão. Se a correlação for alta, é um '1'.
            # O limiar pode ser um valor pequeno, apenas para superar o ruído.
            threshold = 1.0 # Este valor é empírico e pode ser ajustado
            
            if correlation > threshold:
                digital_signal[i] = 1
                demodulated_bits += '1'
            else:
                digital_signal[i] = -1 if mod_digital_type == "NRZ-Polar" else 0
                demodulated_bits += '0'

        t_digital = np.arange(num_bits) * (1.0 / bit_rate)
        return demodulated_bits, digital_signal, t_digital
    # <<< FIM DA CORREÇÃO PRINCIPAL >>>