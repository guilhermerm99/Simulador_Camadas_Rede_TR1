# CamadaFisica/modulacoes_digitais.py
import numpy as np # numpy é permitido para operações matemáticas e array-like, se necessário.
                     # Embora neste arquivo específico não seja estritamente usado para os cálculos primários,
                     # é um bom hábito importar se há chance de uso futuro para gráficos ou outras ops.

class ModulacoesDigitais:
    """
    Implementa diferentes esquemas de modulação digital de banda-base
    para simular a camada física de transmissão de dados.

    As modulações convertem uma sequência de bits (0s e 1s) em um sinal elétrico
    representado por uma lista de valores de tensão.
    """

    def __init__(self):
        """
        Inicializa a classe ModulacoesDigitais.
        Define parâmetros básicos para os níveis de tensão dos sinais.
        """
        # Níveis de tensão para representação dos bits nos sinais modulados.
        self.POSITIVE_VOLTAGE = 1.0  # Representa nível 'alto' ou +V
        self.NEGATIVE_VOLTAGE = -1.0 # Representa nível 'baixo' ou -V
        self.ZERO_VOLTAGE = 0.0      # Representa nível 'zero'

    # --- Métodos de Codificação (Transmissor - TX) ---

    def nrz_polar(self, bits: str) -> list[float]:
        """
        Simula a codificação Non-Return-to-Zero Polar (NRZ-Polar).

        Nesta codificação:
        - O bit '1' é representado por um nível de tensão positivo (+V).
        - O bit '0' é representado por um nível de tensão negativo (-V).
        O sinal não retorna a zero entre os bits, mantendo o nível de tensão constante
        durante toda a duração do bit.

        Args:
            bits (str): Uma string contendo '0's e '1's que representa a sequência de bits a ser modulada.

        Returns:
            list[float]: Uma lista de valores float que representam o sinal modulado.
                         Cada valor na lista corresponde à amplitude do sinal para a duração de um bit.

        Raises:
            ValueError: Se a string de entrada contiver caracteres que não sejam '0' ou '1'.
        """
        signal = []
        for bit in bits:
            if bit == '1':
                signal.append(self.POSITIVE_VOLTAGE)
            elif bit == '0':
                signal.append(self.NEGATIVE_VOLTAGE)
            else:
                raise ValueError("A sequência de bits deve conter apenas '0's ou '1's.")
        return signal

    def manchester(self, bits: str) -> list[float]:
        """
        Simula a codificação Manchester.

        Nesta codificação, cada bit é representado por uma transição de tensão no meio
        do seu período de tempo, garantindo um "clock" embutido no sinal (autossincronização).
        Para fins de simulação visual (e compatibilidade com o diagrama de moodle ):
        - O bit '0' é representado por uma transição de nível alto (+V) para nível baixo (-V).
          Isso é simulado como [1.0, -1.0] em duas "sub-amostras".
        - O bit '1' é representado por uma transição de nível baixo (-V) para nível alto (+V).
          Isso é simulado como [-1.0, 1.0] em duas "sub-amostras".
        Portanto, cada bit de entrada gera dois valores no sinal de saída.

        Args:
            bits (str): Uma string contendo '0's e '1's a ser modulada.

        Returns:
            list[float]: Uma lista de valores float que representam o sinal modulado.
                         Cada bit de entrada corresponde a dois valores no sinal de saída.

        Raises:
            ValueError: Se a string de entrada contiver caracteres que não sejam '0' ou '1'.
        """
        signal = []
        for bit in bits:
            if bit == '1':
                signal.extend([self.NEGATIVE_VOLTAGE, self.POSITIVE_VOLTAGE])  # Transição de baixo para alto
            elif bit == '0':
                signal.extend([self.POSITIVE_VOLTAGE, self.NEGATIVE_VOLTAGE])  # Transição de alto para baixo
            else:
                raise ValueError("A sequência de bits deve conter apenas '0's ou '1's.")
        return signal

    def bipolar(self, bits: str) -> list[float]:
        """
        Simula a codificação Bipolar (também conhecida como Alternate Mark Inversion - AMI).

        Nesta codificação:
        - O bit '0' é representado por um nível de tensão zero (0V).
        - O bit '1' é representado por pulsos alternados de tensão positiva (+V) e negativa (-V).
          Ou seja, o primeiro '1' pode ser +V, o próximo '1' será -V, o próximo +V, e assim por diante.
        Isso ajuda a resolver o problema de longas sequências de '1's que poderiam causar perda de sincronia.

        Args:
            bits (str): Uma string contendo '0's e '1's a ser modulada.

        Returns:
            list[float]: Uma lista de valores float que representam o sinal modulado.
                         Cada bit de entrada corresponde a um valor no sinal de saída.

        Raises:
            ValueError: Se a string de entrada contiver caracteres que não sejam '0' ou '1'.
        """
        signal = []
        # last_one_voltage controla a alternância dos pulsos para o bit '1'.
        # Inicia com +V para que o primeiro '1' seja positivo.
        last_one_voltage = self.POSITIVE_VOLTAGE 
        
        for bit in bits:
            if bit == '0':
                signal.append(self.ZERO_VOLTAGE)
            elif bit == '1':
                signal.append(last_one_voltage)
                last_one_voltage *= -1.0  # Alterna o sinal para o próximo '1'
            else:
                raise ValueError("A sequência de bits deve conter apenas '0's ou '1's.")
        return signal

    # --- Métodos de Decodificação (Receptor - RX) ---

    def decodificar_nrz_polar(self, signal: list[float]) -> str:
        """
        Decodifica um sinal NRZ-Polar de volta para a sequência de bits original.

        Assume que:
        - Valores de sinal >= 0 (e.g., 1.0) representam o bit '1'.
        - Valores de sinal < 0 (e.g., -1.0) representam o bit '0'.

        Args:
            signal (list[float]): Uma lista de valores float que representa o sinal NRZ-Polar recebido.

        Returns:
            str: A string de bits decodificada ('0's e '1's).
        """
        bits = ""
        for val in signal:
            # Um pequeno limiar pode ser usado em casos reais para lidar com ruído,
            # mas para uma simulação ideal, a verificação de sinal é direta.
            if val >= self.ZERO_VOLTAGE: # Sinal positivo ou zero é interpretado como '1'
                bits += '1'
            else: # Sinal negativo é interpretado como '0'
                bits += '0'
        return bits

    def decodificar_manchester(self, signal: list[float]) -> str:
        """
        Decodifica um sinal Manchester de volta para a sequência de bits original.

        Assume que cada bit original foi codificado em duas amostras no sinal:
        - Uma transição de nível baixo (-V) para alto (+V) dentro das duas amostras decodifica para '1'.
        - Uma transição de nível alto (+V) para baixo (-V) dentro das duas amostras decodifica para '0'.

        Args:
            signal (list[float]): Uma lista de valores float que representa o sinal Manchester recebido.
                                  Espera-se que o comprimento da lista seja par, pois cada bit ocupa 2 amostras.

        Returns:
            str: A string de bits decodificada ('0's e '1's).
        """
        bits = ""
        # Itera sobre o sinal de duas em duas amostras, pois cada bit original ocupa duas amostras.
        for i in range(0, len(signal), 2):
            # Garante que há pelo menos duas amostras para processar um bit completo.
            if i + 1 < len(signal):
                first_sample = signal[i]
                second_sample = signal[i+1]

                # Regra de decodificação Manchester:
                if first_sample < second_sample: # Ex: -1.0 para 1.0 (transição de baixo para alto)
                    bits += '1'
                elif first_sample > second_sample: # Ex: 1.0 para -1.0 (transição de alto para baixo)
                    bits += '0'
                else:
                    # Se não houver transição (primeira amostra == segunda amostra),
                    # isso indica um sinal corrompido ou uma sequência inesperada.
                    # Para fins de simulação, podemos ignorar ou sinalizar um erro.
                    # Aqui, optamos por não adicionar um bit, o que pode truncar a saída.
                    # Em um sistema real, isso exigiria tratamento de erro ou ressincronização.
                    print(f"Aviso (Manchester Decoder): Nenhuma transição detectada ou sinal inválido nas amostras {i} e {i+1}. Ignorando este segmento.")
            else:
                # Sinal incompleto (número ímpar de amostras ou última amostra sozinha).
                # Isso pode ser devido a truncamento ou erro na transmissão.
                # print(f"Aviso (Manchester Decoder): Sinal incompleto no final (amostra {i}).")
                pass # Não adiciona um bit para amostras incompletas
        return bits

    def decodificar_bipolar(self, signal: list[float]) -> str:
        """
        Decodifica um sinal Bipolar (AMI) de volta para a sequência de bits original.

        Nesta codificação, qualquer pulso de tensão diferente de zero (+V ou -V)
        representa um bit '1', e um nível de tensão zero (0V) representa um bit '0'.

        Args:
            signal (list[float]): Uma lista de valores float que representa o sinal Bipolar recebido.

        Returns:
            str: A string de bits decodificada ('0's e '1's).
        """
        bits = ""
        for val in signal:
            if val == self.ZERO_VOLTAGE:
                bits += '0'
            else: # Se o valor não é zero, é um '1' (seja +V ou -V)
                bits += '1'
        return bits


# --- Mapeamento de protocolos para uso no simulador ---
# Cria uma instância da classe ModulacoesDigitais.
_modulacoes_digitais_instance = ModulacoesDigitais()

MODULACOES_DIGITAIS_TX = {
    'NRZ-Polar': _modulacoes_digitais_instance.nrz_polar,
    'Manchester': _modulacoes_digitais_instance.manchester,
    'Bipolar': _modulacoes_digitais_instance.bipolar
}

MODULACOES_DIGITAIS_RX = {
    'NRZ-Polar': _modulacoes_digitais_instance.decodificar_nrz_polar,
    'Manchester': _modulacoes_digitais_instance.decodificar_manchester,
    'Bipolar': _modulacoes_digitais_instance.decodificar_bipolar
}