import numpy as np

class DigitalEncoder:
    """Implementa os esquemas de codificação de linha (modulação em banda base).
    Atua na Camada Física, convertendo bits digitais em sinais elétricos apropriados.
    """

    def encode(self, bits, encoding_type, samples_per_bit=10):
        """
        Interface para selecionar o tipo de codificação de linha desejada.
        Parâmetros:
        - bits: sequência binária a ser codificada.
        - encoding_type: string que define o tipo de codificação (NRZ-Polar, Manchester, Bipolar).
        - samples_per_bit: define quantas amostras serão usadas para representar cada bit.
        """
        if encoding_type == "NRZ-Polar":
            return self.nrz_polar(bits, samples_per_bit)
        elif encoding_type == "Manchester":
            return self.manchester(bits, samples_per_bit)
        elif encoding_type == "Bipolar":
            return self.bipolar_ami(bits, samples_per_bit)
        else:
            raise ValueError(f"Tipo de codificação desconhecido: {encoding_type}")

    def nrz_polar(self, bits, samples_per_bit=10):
        """
        Implementa NRZ-Polar (Non-Return to Zero Polar):
        - Bit '1' → nível positivo constante (+1)
        - Bit '0' → nível negativo constante (-1)
        O sinal é mantido constante durante toda a duração do bit.
        Cada nível é replicado 'samples_per_bit' vezes para representar o tempo.
        """
        signal = []
        for bit in bits:
            val = 1.0 if int(bit) == 1 else -1.0
            signal.extend([val] * samples_per_bit)
        return np.array(signal)

    def manchester(self, bits, samples_per_bit=10):
        """
        Implementa codificação Manchester:
        Cada bit é dividido em duas metades:
        - Bit '0' → primeiro +1, depois -1
        - Bit '1' → primeiro -1, depois +1
        A transição no meio do bit garante sincronização com o receptor.
        """
        half_spb = samples_per_bit // 2
        signal = []
        for bit in bits:
            if int(bit) == 0:
                signal.extend([1.0] * half_spb)   # Primeira metade positiva
                signal.extend([-1.0] * half_spb)  # Segunda metade negativa
            else:
                signal.extend([-1.0] * half_spb)  # Primeira metade negativa
                signal.extend([1.0] * half_spb)   # Segunda metade positiva
        return np.array(signal)

    def bipolar_ami(self, bits, samples_per_bit=10):
        """
        Implementa Bipolar AMI (Alternate Mark Inversion):
        - Bit '0' → nível zero (sem pulso)
        - Bit '1' → alterna entre +1 e -1 a cada ocorrência
        Utiliza polaridade alternada para representar bits '1', facilitando detecção de erro.
        """
        signal = []
        last_pulse_level = -1.0  # Começa com -1 para que o primeiro pulso seja +1
        for bit in bits:
            if int(bit) == 0:
                signal.extend([0.0] * samples_per_bit)
            else:
                last_pulse_level *= -1.0  # Alterna a polaridade
                signal.extend([last_pulse_level] * samples_per_bit)
        return np.array(signal)
