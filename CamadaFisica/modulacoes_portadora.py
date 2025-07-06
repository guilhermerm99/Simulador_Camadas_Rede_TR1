# CamadaFisica/modulacoes_portadora.py

import numpy as np
import math

class CarrierModulator:
    """Implementa e demodula as modulações de portadora (ASK, FSK, 8-QAM)."""

    def __init__(self, bit_rate, carrier_freq, amplitude, sampling_rate):
        self.bit_rate = bit_rate
        self.carrier_freq = carrier_freq
        self.amplitude = amplitude
        self.sampling_rate = sampling_rate
        self.samples_per_bit = int(self.sampling_rate / self.bit_rate)
        
        self.QAM8_MAP = {
            '000': complex(-1, 1), '001': complex(-1, 3), '011': complex(1, 3), '010': complex(1, 1),
            '100': complex(-1, -1), '101': complex(-1, -3), '111': complex(1, -3), '110': complex(1, -1),
        }
        self.INV_QAM8_MAP = {v: k for k, v in self.QAM8_MAP.items()}

    def modulate(self, signal_source, modulation_type):
        """
        Chama o método de modulação apropriado.
        Recebe um sinal já preparado (array numpy para ASK/FSK, string para 8-QAM).
        """
        if modulation_type == "ASK":
            return self.modulate_ask(signal_source)
        elif modulation_type == "FSK":
            return self.modulate_fsk(signal_source)
        elif modulation_type == "8-QAM":
            return self.modulate_8qam(signal_source)
        else:
            raise ValueError(f"Tipo de modulação desconhecido: {modulation_type}")
        
    def modulate_ask(self, digital_signal):
        num_bits = len(digital_signal)
        num_total_samples = num_bits * self.samples_per_bit
        t = np.linspace(0, num_bits / self.bit_rate, num_total_samples, endpoint=False)
        
        amplitude_signal = np.repeat(digital_signal * self.amplitude, self.samples_per_bit)
        carrier_wave = np.sin(2 * np.pi * self.carrier_freq * t)
        modulated_signal = amplitude_signal * carrier_wave
        
        return t, modulated_signal

    def modulate_fsk(self, digital_signal):
        num_bits = len(digital_signal)
        num_total_samples = num_bits * self.samples_per_bit
        t = np.linspace(0, num_bits / self.bit_rate, num_total_samples, endpoint=False)
        
        f_dev = self.bit_rate
        f1 = self.carrier_freq + f_dev
        f_minus1 = self.carrier_freq - f_dev
        
        modulated_signal = np.zeros_like(t)
        for i, level in enumerate(digital_signal):
            start, end = i * self.samples_per_bit, (i + 1) * self.samples_per_bit
            freq = f1 if level == 1 else f_minus1
            modulated_signal[start:end] = self.amplitude * np.sin(2 * np.pi * freq * t[start:end])
            
        return t, modulated_signal

    def modulate_8qam(self, bits):
        padding = len(bits) % 3
        if padding != 0: bits += '0' * (3 - padding)
        
        symbols = [bits[i:i+3] for i in range(0, len(bits), 3)]
        qam_points = [self.QAM8_MAP.get(s, complex(0,0)) for s in symbols]
        
        num_symbols = len(qam_points)
        samples_per_symbol = self.samples_per_bit * 3
        num_total_samples = num_symbols * samples_per_symbol
        t = np.linspace(0, num_symbols * 3 / self.bit_rate, num_total_samples, endpoint=False)
        
        modulated_signal = np.zeros(num_total_samples)
        for i, point in enumerate(qam_points):
            start, end = i * samples_per_symbol, (i + 1) * samples_per_symbol
            i_comp = point.real * self.amplitude; q_comp = point.imag * self.amplitude
            cos_carrier = np.cos(2 * np.pi * self.carrier_freq * t[start:end])
            sin_carrier = np.sin(2 * np.pi * self.carrier_freq * t[start:end])
            modulated_signal[start:end] = i_comp * cos_carrier - q_comp * sin_carrier
            
        return t, modulated_signal, qam_points

    def demodulate(self, received_signal, modulation_type, config):
        """Despachante para o demodulador apropriado."""
        if modulation_type == "ASK":
            return self._demodulate_ask(received_signal, config)
        elif modulation_type == "FSK":
            return self._demodulate_fsk(received_signal, config)
        elif modulation_type == "8-QAM":
            return self._demodulate_8qam(received_signal, config)
        else:
            raise ValueError(f"Tipo de demodulação desconhecido: {modulation_type}")

    def _demodulate_ask(self, received_signal, config):
        bit_rate = config['bit_rate']; sampling_rate = config['sampling_rate']
        carrier_freq = config['freq_base']; mod_digital_type = config.get('mod_digital_type', 'NRZ-Polar')
        samples_per_bit = int(sampling_rate / bit_rate)
        num_bits = len(received_signal) // samples_per_bit
        
        demodulated_bits = ""; digital_signal_rx = np.zeros(num_bits)
        t_bit = np.linspace(0, 1.0/bit_rate, samples_per_bit, endpoint=False)
        local_carrier = np.sin(2 * np.pi * carrier_freq * t_bit)
        threshold = np.sum((self.amplitude * local_carrier) * local_carrier) / 2.5

        for i in range(num_bits):
            start, end = i * samples_per_bit, (i + 1) * samples_per_bit
            if end > len(received_signal): break
            segment = received_signal[start:end]
            correlation = np.sum(segment * local_carrier)
            
            if correlation > threshold:
                demodulated_bits += '1'
                digital_signal_rx[i] = 1
            else:
                demodulated_bits += '0'
                digital_signal_rx[i] = -1 if mod_digital_type == "NRZ-Polar" else 0
        
        t_digital = np.arange(len(digital_signal_rx)) * (1.0 / bit_rate)
        return demodulated_bits, digital_signal_rx, t_digital

    def _demodulate_fsk(self, received_signal, config):
        bit_rate = config['bit_rate']; sampling_rate = config['sampling_rate']
        carrier_freq = config['freq_base']; mod_digital_type = config.get('mod_digital_type', 'NRZ-Polar')
        samples_per_bit = int(sampling_rate / bit_rate)
        num_bits = len(received_signal) // samples_per_bit

        demodulated_bits = ""; digital_signal_rx = np.zeros(num_bits)
        t_bit = np.linspace(0, 1.0/bit_rate, samples_per_bit, endpoint=False)
        
        f_dev = bit_rate; f1 = carrier_freq + f_dev; f0 = carrier_freq - f_dev
        local_carrier_1 = np.sin(2 * np.pi * f1 * t_bit)
        local_carrier_0 = np.sin(2 * np.pi * f0 * t_bit)

        for i in range(num_bits):
            start, end = i * samples_per_bit, (i + 1) * samples_per_bit
            if end > len(received_signal): break
            segment = received_signal[start:end]
            correlation1 = np.sum(segment * local_carrier_1)
            correlation0 = np.sum(segment * local_carrier_0)
            
            if correlation1 > correlation0:
                demodulated_bits += '1'
                digital_signal_rx[i] = 1
            else:
                demodulated_bits += '0'
                digital_signal_rx[i] = -1 if mod_digital_type == "NRZ-Polar" else 0

        t_digital = np.arange(len(digital_signal_rx)) * (1.0 / bit_rate)
        return demodulated_bits, digital_signal_rx, t_digital

    def _demodulate_8qam(self, received_signal, config):
        bit_rate = config['bit_rate']
        sampling_rate = config['sampling_rate']
        carrier_freq = config['freq_base']
        samples_per_symbol = int(sampling_rate / bit_rate) * 3
        num_symbols = len(received_signal) // samples_per_symbol

        demodulated_bits = ""
        constellation_points = list(self.INV_QAM8_MAP.keys())

        for i in range(num_symbols):
            start_sample = i * samples_per_symbol
            end_sample = (i + 1) * samples_per_symbol
            
            if end_sample > len(received_signal):
                break
            
            segment = received_signal[start_sample:end_sample]

            symbol_duration = 3.0 / bit_rate
            t_start = i * symbol_duration
            t_end = (i + 1) * symbol_duration
            t_local = np.linspace(t_start, t_end, samples_per_symbol, endpoint=False)

            cos_carrier = np.cos(2 * np.pi * carrier_freq * t_local)
            sin_carrier = np.sin(2 * np.pi * carrier_freq * t_local)

            i_rx = np.sum(segment * cos_carrier)
            q_rx = np.sum(segment * -sin_carrier)
            
            basis_energy = np.sum(cos_carrier**2)
            norm_factor = self.amplitude * basis_energy
            
            if norm_factor > 1e-9:
                received_point = complex(i_rx / norm_factor, q_rx / norm_factor)
            else:
                received_point = complex(0, 0)

            distances = [abs(received_point - p) for p in constellation_points]
            closest_point_index = np.argmin(distances)
            closest_point = constellation_points[closest_point_index]
            
            demodulated_bits += self.INV_QAM8_MAP[closest_point]
            
            # Debugging: Log constellation points
            print(f"Symbol {i}: Received point: {received_point}, Closest point: {closest_point}, Bits: {self.INV_QAM8_MAP[closest_point]}")

        # Trim padding based on expected payload length (if available in config)
        expected_payload_len = config.get('original_payload_len', len(demodulated_bits))
        if len(demodulated_bits) > expected_payload_len:
            demodulated_bits = demodulated_bits[:expected_payload_len]
        
        # Debugging: Log demodulated bits
        print(f"Demodulated bits: {demodulated_bits}")

        num_bits = len(demodulated_bits)
        digital_signal_rx = np.array([1 if b == '1' else -1 for b in demodulated_bits])
        t_digital = np.arange(num_bits) * (1.0 / bit_rate)
        
        return demodulated_bits, digital_signal_rx, t_digital