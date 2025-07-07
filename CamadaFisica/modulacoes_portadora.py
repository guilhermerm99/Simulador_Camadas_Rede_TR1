# CamadaFisica/modulacoes_portadora.py

import numpy as np
import math

class CarrierModulator:
    """
    Implementa modulações de portadora ASK, FSK e 8-QAM.
    Atua na Camada Física, convertendo sinais digitais em formas analógicas apropriadas para transmissão.
    """

    def __init__(self, bit_rate, carrier_freq, amplitude, sampling_rate):
        """
        Inicializa os parâmetros da modulação.

        - bit_rate: Taxa de bits (bps)
        - carrier_freq: Frequência da portadora (Hz)
        - amplitude: Amplitude do sinal (V)
        - sampling_rate: Taxa de amostragem (samples/s)
        """
        self.bit_rate = bit_rate
        self.carrier_freq = carrier_freq
        self.amplitude = amplitude
        self.sampling_rate = sampling_rate
        self.samples_per_bit = int(sampling_rate / bit_rate)

        # Constelação 8-QAM (mapa de 3 bits para pontos complexos)
        self.QAM8_MAP = {
            '000': complex(-1, 1), '001': complex(-1, 3), '011': complex(1, 3), '010': complex(1, 1),
            '100': complex(-1, -1), '101': complex(-1, -3), '111': complex(1, -3), '110': complex(1, -1),
        }
        self.INV_QAM8_MAP = {v: k for k, v in self.QAM8_MAP.items()}

    def modulate(self, signal_source, modulation_type):
        """
        Chama a modulação apropriada com base no tipo.
        - ASK/FSK esperam array de bits em forma de sinal (NRZ).
        - 8-QAM espera string de bits.
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
        """
        Modulação ASK (Amplitude Shift Keying):
        A amplitude da portadora varia com o nível do bit (OOK).
        """
        num_bits = len(digital_signal)
        t = np.linspace(0, num_bits / self.bit_rate, num_bits * self.samples_per_bit, endpoint=False)

        amplitude_signal = np.repeat(digital_signal * self.amplitude, self.samples_per_bit)
        carrier = np.sin(2 * np.pi * self.carrier_freq * t)
        modulated = amplitude_signal * carrier
        return t, modulated

    def modulate_fsk(self, digital_signal):
        """
        Modulação FSK (Frequency Shift Keying):
        A frequência da portadora depende do bit transmitido.
        """
        num_bits = len(digital_signal)
        t = np.linspace(0, num_bits / self.bit_rate, num_bits * self.samples_per_bit, endpoint=False)

        f_dev = self.bit_rate  # Desvio de frequência
        f1 = self.carrier_freq + f_dev
        f0 = self.carrier_freq - f_dev

        modulated = np.zeros_like(t)
        for i, level in enumerate(digital_signal):
            start, end = i * self.samples_per_bit, (i + 1) * self.samples_per_bit
            freq = f1 if level == 1 else f0
            modulated[start:end] = self.amplitude * np.sin(2 * np.pi * freq * t[start:end])
        return t, modulated

    def modulate_8qam(self, bits):
        """
        Modulação 8-QAM:
        Cada grupo de 3 bits é mapeado para um ponto (I,Q) na constelação.
        """
        if len(bits) % 3 != 0:
            bits += '0' * (3 - len(bits) % 3)  # Padding

        symbols = [bits[i:i+3] for i in range(0, len(bits), 3)]
        qam_points = [self.QAM8_MAP.get(s, complex(0, 0)) for s in symbols]

        samples_per_symbol = self.samples_per_bit * 3
        t = np.linspace(0, len(symbols) * 3 / self.bit_rate, len(symbols) * samples_per_symbol, endpoint=False)
        modulated = np.zeros(len(t))

        for i, point in enumerate(qam_points):
            start = i * samples_per_symbol
            end = (i + 1) * samples_per_symbol
            i_comp = point.real * self.amplitude
            q_comp = point.imag * self.amplitude

            cos = np.cos(2 * np.pi * self.carrier_freq * t[start:end])
            sin = np.sin(2 * np.pi * self.carrier_freq * t[start:end])
            modulated[start:end] = i_comp * cos - q_comp * sin

        return t, modulated, qam_points

    def demodulate(self, received, modulation_type, config):
        """
        Chama o demodulador apropriado.
        """
        if modulation_type == "ASK":
            return self._demodulate_ask(received, config)
        elif modulation_type == "FSK":
            return self._demodulate_fsk(received, config)
        elif modulation_type == "8-QAM":
            return self._demodulate_8qam(received, config)
        else:
            raise ValueError(f"Tipo de demodulação desconhecido: {modulation_type}")

    def _demodulate_ask(self, received, config):
        """
        Demodulação coerente de ASK usando correlação com portadora local.
        """
        bit_rate = config['bit_rate']
        sampling_rate = config['sampling_rate']
        freq = config['freq_base']
        digital_type = config.get('mod_digital_type', 'NRZ-Polar')

        samples_per_bit = int(sampling_rate / bit_rate)
        num_bits = len(received) // samples_per_bit
        t_bit = np.linspace(0, 1 / bit_rate, samples_per_bit, endpoint=False)
        carrier = np.sin(2 * np.pi * freq * t_bit)

        threshold = np.sum((self.amplitude * carrier) * carrier) / 2
        bits = ""; signal_rx = np.zeros(num_bits)

        for i in range(num_bits):
            seg = received[i * samples_per_bit : (i + 1) * samples_per_bit]
            corr = np.sum(seg * carrier)
            if corr > threshold:
                bits += '1'; signal_rx[i] = 1
            else:
                bits += '0'; signal_rx[i] = -1 if digital_type == "NRZ-Polar" else 0

        t_digital = np.arange(num_bits) / bit_rate
        return bits, signal_rx, t_digital

    def _demodulate_fsk(self, received, config):
        """
        Demodulação FSK por correlação com duas portadoras (f0 e f1).
        """
        bit_rate = config['bit_rate']
        sampling_rate = config['sampling_rate']
        freq = config['freq_base']
        digital_type = config.get('mod_digital_type', 'NRZ-Polar')

        samples_per_bit = int(sampling_rate / bit_rate)
        num_bits = len(received) // samples_per_bit
        t_bit = np.linspace(0, 1 / bit_rate, samples_per_bit, endpoint=False)

        f_dev = bit_rate
        f1 = freq + f_dev; f0 = freq - f_dev
        c1 = np.sin(2 * np.pi * f1 * t_bit)
        c0 = np.sin(2 * np.pi * f0 * t_bit)

        bits = ""; signal_rx = np.zeros(num_bits)

        for i in range(num_bits):
            seg = received[i * samples_per_bit : (i + 1) * samples_per_bit]
            corr1 = np.sum(seg * c1)
            corr0 = np.sum(seg * c0)
            if corr1 > corr0:
                bits += '1'; signal_rx[i] = 1
            else:
                bits += '0'; signal_rx[i] = -1 if digital_type == "NRZ-Polar" else 0

        t_digital = np.arange(num_bits) / bit_rate
        return bits, signal_rx, t_digital

    def _demodulate_8qam(self, received, config):
        """
        Demodulação coerente de 8-QAM por projeção I/Q e detecção por distância mínima.
        """
        bit_rate = config['bit_rate']
        sampling_rate = config['sampling_rate']
        freq = config['freq_base']
        samples_per_symbol = int(sampling_rate / bit_rate) * 3
        num_symbols = len(received) // samples_per_symbol

        constellation = list(self.INV_QAM8_MAP.keys())
        bits = ""

        for i in range(num_symbols):
            start = i * samples_per_symbol
            end = (i + 1) * samples_per_symbol
            seg = received[start:end]
            if len(seg) < samples_per_symbol: break

            t = np.linspace(i * 3 / bit_rate, (i + 1) * 3 / bit_rate, samples_per_symbol, endpoint=False)
            cos = np.cos(2 * np.pi * freq * t)
            sin = np.sin(2 * np.pi * freq * t)

            i_comp = np.sum(seg * cos)
            q_comp = np.sum(seg * -sin)
            norm = self.amplitude * np.sum(cos**2)

            point = complex(i_comp / norm, q_comp / norm) if norm > 1e-9 else 0
            closest = min(constellation, key=lambda c: abs(point - c))
            bits += self.INV_QAM8_MAP[closest]

        expected_len = config.get('original_payload_len', len(bits))
        bits = bits[:expected_len]

        signal_rx = np.array([1 if b == '1' else -1 for b in bits])
        t_digital = np.arange(len(bits)) / bit_rate
        return bits, signal_rx, t_digital
