# CamadaFisica/modulacoes_digitais.py

import numpy as np

class DigitalEncoder:
    """Implementa os esquemas de codificação de linha (banda-base)."""

    def encode(self, bits, encoding_type):
        """Chama o método de codificação apropriado."""
        if encoding_type == "NRZ-Polar":
            return self.nrz_polar(bits)
        elif encoding_type == "Manchester":
            return self.manchester(bits)
        elif encoding_type == "Bipolar":
            return self.bipolar_ami(bits)
        else:
            raise ValueError(f"Tipo de codificação desconhecido: {encoding_type}")

    def nrz_polar(self, bits):
        """
        Codificação NRZ-Polar:
        - Bit '1' -> Nível de tensão positivo (+1V)
        - Bit '0' -> Nível de tensão negativo (-1V)
        """
        return np.array([1 if int(bit) == 1 else -1 for bit in bits])

    def manchester(self, bits):
        """
        Codificação Manchester:
        - Bit '0' -> Transição de baixo para alto (-1V para +1V)
        - Bit '1' -> Transição de alto para baixo (+1V para -1V)
        """
        manchester_signal = []
        for bit in bits:
            if int(bit) == 0:
                manchester_signal.extend([-1, 1])
            else:
                manchester_signal.extend([1, -1])
        return np.array(manchester_signal)

    def bipolar_ami(self, bits):
        """
        Codificação Bipolar AMI:
        - Bit '0' -> 0V
        - Bit '1' -> alterna entre +1V e -1V
        """
        signal = []
        last_pulse_level = -1
        for bit in bits:
            if int(bit) == 0:
                signal.append(0)
            else:
                last_pulse_level *= -1
                signal.append(last_pulse_level)
        return np.array(signal)
