# CamadaFisica/modulacoes_digitais.py

import numpy as np

class DigitalEncoder:
    """Implementa os esquemas de codificação de linha (modulação em banda base).
    Atua na Camada Física, convertendo bits digitais em sinais elétricos apropriados.
    """

    def encode(self, bits, encoding_type):
        """
        Seleciona o esquema de codificação de linha com base no tipo informado.
        """
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
        NRZ-Polar (Non-Return to Zero Polar):
        - Bit '1' → nível positivo (+V)
        - Bit '0' → nível negativo (-V)

        Vantagem: simples implementação.
        Limitação: ausência de transições em sequências longas dificulta a sincronização no receptor.
        """
        return np.array([1.0 if int(bit) == 1 else -1.0 for bit in bits])

    def manchester(self, bits):
        """
        Manchester:
        Codificação com transição obrigatória no meio do intervalo de bit.
        Facilita a sincronização do clock pois embute a transição no próprio dado.

        Convenção utilizada (com base na disciplina):
        - Bit '0' → transição de +V para -V (alto → baixo)
        - Bit '1' → transição de -V para +V (baixo → alto)
        """
        manchester_signal = []
        for bit in bits:
            if int(bit) == 0:
                manchester_signal.extend([1.0, -1.0])  # Bit 0: alto → baixo
            else:
                manchester_signal.extend([-1.0, 1.0])  # Bit 1: baixo → alto
        return np.array(manchester_signal)

    def bipolar_ami(self, bits):
        """
        Bipolar AMI (Alternate Mark Inversion):
        - Bit '0' → nível zero (0V)
        - Bit '1' → alterna entre +V e -V (evita componente DC)

        Benefícios:
        - Evita longas sequências com o mesmo nível.
        - Elimina componente contínua (DC), útil em transmissão com acoplamento capacitivo.
        """
        signal = []
        last_pulse_level = -1.0  # Alternância começa com +1 no primeiro bit '1'
        for bit in bits:
            if int(bit) == 0:
                signal.append(0.0)
            else:
                last_pulse_level *= -1.0  # Inverte sinal do último pulso
                signal.append(last_pulse_level)
        return np.array(signal)
