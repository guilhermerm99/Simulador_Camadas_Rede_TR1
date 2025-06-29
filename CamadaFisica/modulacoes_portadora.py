# CamadaFisica/modulacoes_portadora.py
import numpy as np

class ModulacoesPortadora:
    """
    Implementa diferentes esquemas de modulação e demodulação por portadora
    para simular a camada física de transmissão de dados.

    A modulação por portadora utiliza uma onda senoidal (portadora) e altera
    suas propriedades (amplitude, frequência, fase) para codificar informações digitais.
    """

    def __init__(self):
        """
        Inicializa a classe ModulacoesPortadora com constantes de simulação.
        Estas constantes definem a resolução do sinal (amostragem) e a duração dos símbolos.
        """
        # Frequência de amostragem da portadora. Define quantos pontos são usados para simular a onda.
        # Um valor mais alto resulta em uma curva senoidal mais suave e precisa.
        self.FS_PORTADORA = 1000  # Amostras por segundo
        
        # Duração de um único símbolo/bit em segundos.
        # Por exemplo, 0.05 segundos significa que cada bit (ou grupo de bits em QAM) dura 50ms.
        self.TEMPO_SIMBOLO = 0.05 

        # Frequência da portadora para ASK e QAM.
        self.FC_DEFAULT = 50 # Hertz

        # Frequências para FSK (f0 para '0', f1 para '1').
        self.F0_FSK = 20 # Hertz
        self.F1_FSK = 40 # Hertz

        # Mapeamento de símbolos para 8-QAM (bits -> (amplitude, fase em graus)).
        # As fases são definidas em graus para maior legibilidade.
        # A amplitude 0.707 é aprox 1/sqrt(2) e 1.0 para dois níveis de amplitude.
        self.QAM8_SYMBOL_MAP = {
            '000': (0.707, 0),    # Amplitude 1, Fase 0 deg
            '001': (0.707, 45),   # Amplitude 1, Fase 45 deg
            '010': (0.707, 90),   # Amplitude 1, Fase 90 deg
            '011': (0.707, 135),  # Amplitude 1, Fase 135 deg
            '100': (1.0, 180),    # Amplitude 2, Fase 180 deg
            '101': (1.0, 225),    # Amplitude 2, Fase 225 deg
            '110': (1.0, 270),    # Amplitude 2, Fase 270 deg
            '111': (1.0, 315)     # Amplitude 2, Fase 315 deg
        }
        # Prepara um mapa de decodificação com fases em radianos para comparação eficiente.
        self.QAM8_DECODE_MAP_RAD = {
            (amp, np.deg2rad(phase_deg)): sym_bits
            for (sym_bits, (amp, phase_deg)) in self.QAM8_SYMBOL_MAP.items()
        }

    # --- Método de Geração de Portadora (Auxiliar) ---
    def _gerar_portadora(self, frequencia: float, amplitude: float, duracao_simbolo: float, fase_rad: float) -> np.ndarray:
    # CORREÇÃO AQUI: Adicionado 'self' como o primeiro parâmetro.
        """
        Função auxiliar para gerar uma onda senoidal (portadora).

        Args:
            frequencia (float): Frequência da onda em Hertz.
            amplitude (float): Amplitude máxima da onda.
            duracao_simbolo (float): Duração do segmento de onda em segundos (correspondente a um símbolo/bit).
            fase_rad (float): Fase inicial da onda em radianos.

        Returns:
            np.ndarray: Um array NumPy de floats representando a onda senoidal amostrada.
        """
        # Calcula o número de amostras para a duração do símbolo.
        num_amostras = int(self.FS_PORTADORA * duracao_simbolo)
        # Gera um vetor de tempo de 0 até duracao_simbolo, com 'num_amostras' pontos.
        t = np.linspace(0, duracao_simbolo, num_amostras, endpoint=False)
        # Calcula a onda senoidal: A * sin(2 * pi * f * t + fase).
        return amplitude * np.sin(2 * np.pi * frequencia * t + fase_rad)

    # --- Métodos de Modulação (Transmissor - TX) ---

    def ask(self, bits: str) -> list[float]:
        """
        Simula a modulação Amplitude Shift Keying (ASK).
        A amplitude da portadora é alterada para representar os bits:
        - '1': Portadora com amplitude máxima (ex: 1.0).
        - '0': Portadora com amplitude mínima (ex: 0.0 - sem sinal).

        Args:
            bits (str): Uma string contendo '0's e '1's para modulação.

        Returns:
            list[float]: O sinal ASK modulado como uma lista de valores de amplitude.

        Raises:
            ValueError: Se a string de entrada contiver caracteres que não sejam '0' ou '1'.
        """
        signal = []
        for bit in bits:
            if bit == '1':
                # Para bit '1', amplitude da portadora é 1.0 (ou outro valor > 0)
                signal.extend(self._gerar_portadora(self.FC_DEFAULT, 1.0, self.TEMPO_SIMBOLO, fase_rad=0))
            elif bit == '0':
                # Para bit '0', amplitude da portadora é 0.0 (sem sinal)
                signal.extend(self._gerar_portadora(self.FC_DEFAULT, 0.0, self.TEMPO_SIMBOLO, fase_rad=0))
            else:
                raise ValueError("A sequência de bits deve conter apenas '0's ou '1's.")
        return signal

    def fsk(self, bits: str) -> list[float]:
        """
        Simula a modulação Frequency Shift Keying (FSK).
        A frequência da portadora é alterada para representar os bits:
        - '1': Frequência f1 (ex: 40 Hz).
        - '0': Frequência f0 (ex: 20 Hz).
        A amplitude permanece constante.

        Args:
            bits (str): Uma string contendo '0's e '1's para modulação.

        Returns:
            list[float]: O sinal FSK modulado como uma lista de valores de amplitude.

        Raises:
            ValueError: Se a string de entrada contiver caracteres que não sejam '0' ou '1'.
        """
        signal = []
        for bit in bits:
            if bit == '1':
                # Para bit '1', usa frequência f1 com amplitude 1.0
                signal.extend(self._gerar_portadora(self.F1_FSK, 1.0, self.TEMPO_SIMBOLO, fase_rad=0))
            elif bit == '0':
                # Para bit '0', usa frequência f0 com amplitude 1.0
                signal.extend(self._gerar_portadora(self.F0_FSK, 1.0, self.TEMPO_SIMBOLO, fase_rad=0))
            else:
                raise ValueError("A sequência de bits deve conter apenas '0's ou '1's.")
        return signal

    def qam_8(self, bits: str) -> list[float]:
        """
        Simula a modulação 8-Quadrature Amplitude Modulation (8-QAM).
        Codifica grupos de 3 bits (símbolos) alterando tanto a amplitude quanto a fase
        de uma única portadora. Existem 8 combinações únicas (2^3 = 8).

        Args:
            bits (str): Uma string de bits para modulação. Se o comprimento não for múltiplo de 3,
                        zeros são adicionados à direita (padding) para completar o último símbolo.

        Returns:
            list[float]: O sinal 8-QAM modulado como uma lista de valores de amplitude.
        """
        # Adiciona padding de zeros se o comprimento dos bits não for múltiplo de 3,
        # para garantir que todos os bits possam ser agrupados em símbolos de 3 bits.
        if len(bits) % 3 != 0:
            bits = bits.ljust((len(bits) + 2) // 3 * 3, '0')

        signal = []
        for i in range(0, len(bits), 3):
            symbol_bits = bits[i:i+3] # Pega um grupo de 3 bits
            
            # Busca a amplitude e fase (em graus) correspondentes ao símbolo no mapa.
            amplitude, phase_deg = self.QAM8_SYMBOL_MAP.get(symbol_bits, (0, 0))
            
            # Converte a fase de graus para radianos, pois a função seno espera radianos.
            phase_rad = np.deg2rad(phase_deg)
            
            # Gera o segmento de portadora para este símbolo e o adiciona ao sinal total.
            signal.extend(self._gerar_portadora(self.FC_DEFAULT, amplitude, self.TEMPO_SIMBOLO, phase_rad))
        return signal

    # --- Métodos de Demodulação (Receptor - RX) ---

    def demodular_ask(self, signal: list[float]) -> str:
        """
        Demodula um sinal ASK de volta para a sequência de bits original.
        A demodulação é baseada na detecção da amplitude média de cada símbolo.
        Se a amplitude média for maior que um certo limiar, é um '1'; caso contrário, é um '0'.

        Args:
            signal (list[float]): O sinal ASK recebido como uma lista de valores de amplitude.

        Returns:
            str: A string de bits decodificada ('0's e '1's).
        """
        bits = ""
        # Calcula o número de amostras por símbolo com base na frequência de amostragem e tempo do símbolo.
        amostras_por_simbolo = int(self.FS_PORTADORA * self.TEMPO_SIMBOLO)
        
        # Itera sobre o sinal em segmentos correspondentes à duração de um símbolo.
        for i in range(0, len(signal), amostras_por_simbolo):
            segment = signal[i:i + amostras_por_simbolo]
            
            # Ignora segmentos vazios (pode ocorrer no final se o sinal for truncado).
            if not segment:
                continue
            
            # Calcula a amplitude média do segmento. Usamos abs() para lidar com valores negativos.
            # O limiar 0.5 é uma heurística para distinguir entre a amplitude 0.0 ('0') e 1.0 ('1').
            # Em cenários reais, este limiar seria mais sofisticado.
            avg_amplitude = np.mean(np.abs(segment))

            if avg_amplitude > 0.5: # Se a amplitude for alta, é um '1'
                bits += '1'
            else: # Se a amplitude for baixa (próxima de zero), é um '0'
                bits += '0'
        return bits

    def demodular_fsk(self, signal: list[float]) -> str:
        """
        Demodula um sinal FSK de volta para a sequência de bits original.
        A demodulação é feita correlacionando o sinal recebido com as formas de onda
        das portadoras esperadas (f0 para '0', f1 para '1').
        O símbolo corresponde à frequência que tem a maior correlação com o segmento do sinal.

        Args:
            signal (list[float]): O sinal FSK recebido como uma lista de valores de amplitude.

        Returns:
            str: A string de bits decodificada ('0's e '1's).
        """
        bits = ""
        # Número de amostras que correspondem a um símbolo (bit) de duração.
        amostras_por_simbolo = int(self.FS_PORTADORA * self.TEMPO_SIMBOLO)
        
        # Loop sobre o sinal recebido em janelas de tempo de um símbolo.
        for i in range(0, len(signal), amostras_por_simbolo):
            # Extrai o segmento de sinal para o símbolo atual.
            segment = np.array(signal[i:i + amostras_por_simbolo])
            
            # Pula segmentos incompletos ou vazios no final do sinal.
            if len(segment) < amostras_por_simbolo:
                continue

            # Gera as portadoras de referência (para '0' e '1') com a mesma duração do símbolo.
            t = np.linspace(0, self.TEMPO_SIMBOLO, amostras_por_simbolo, endpoint=False)
            
            # Importante: para uma demodulação FSK ideal, as fases destas senoides de referência
            # deveriam ser sincronizadas com a fase da portadora real, o que é complexo.
            # Aqui, assumimos fase zero para simplicidade na simulação.
            sin_f0 = np.sin(2 * np.pi * self.F0_FSK * t)
            sin_f1 = np.sin(2 * np.pi * self.F1_FSK * t)

            # Calcula a correlação (produto interno) do segmento recebido com cada portadora de referência.
            # A frequência com a maior correlação indica qual bit foi transmitido.
            corr_f0 = np.sum(segment * sin_f0)
            corr_f1 = np.sum(segment * sin_f1)

            if corr_f1 > corr_f0: # Se a correlação com f1 for maior, é um '1'
                bits += '1'
            else: # Caso contrário, é um '0'
                bits += '0'
        return bits

    def demodular_qam_8(self, signal: list[float]) -> str:
        """
        Demodula um sinal 8-QAM de volta para a sequência de bits original.
        Utiliza componentes I e Q para estimar a amplitude e fase de cada símbolo,
        e então encontra o símbolo mais próximo no mapeamento da constelação 8-QAM.

        Args:
            signal (list[float]): O sinal 8-QAM recebido como uma lista de valores de amplitude.

        Returns:
            str: A string de bits decodificada ('0's e '1's), agrupados em símbolos de 3 bits.
        """
        bits = ""
        # Número de amostras que correspondem a um símbolo (3 bits).
        amostras_por_simbolo = int(self.FS_PORTADORA * self.TEMPO_SIMBOLO)
        
        # Loop sobre o sinal recebido em janelas de tempo de um símbolo.
        for i in range(0, len(signal), amostras_por_simbolo):
            # Extrai o segmento de sinal para o símbolo atual.
            segment = np.array(signal[i:i + amostras_por_simbolo])
            
            # Pula segmentos incompletos ou vazios no final do sinal.
            if len(segment) < amostras_por_simbolo:
                continue

            # Gera as portadoras em fase (cosseno) e em quadratura (seno) para desmodulação.
            t = np.linspace(0, self.TEMPO_SIMBOLO, amostras_por_simbolo, endpoint=False)
            carrier_cos = np.cos(2 * np.pi * self.FC_DEFAULT * t)
            carrier_sin = np.sin(2 * np.pi * self.FC_DEFAULT * t)

            # Calcula as componentes I (in-phase) e Q (quadrature) do sinal.
            # A multiplicação por 2 é para normalização (poder médio do sinal).
            I_component = 2 * np.mean(segment * carrier_cos)
            Q_component = 2 * np.mean(segment * carrier_sin)

            # Estima a amplitude e a fase do símbolo recebido no plano I-Q.
            estimated_amplitude = np.sqrt(I_component**2 + Q_component**2)
            
            # Calcula a fase usando arctan2 para lidar corretamente com todos os quadrantes.
            # Trata o caso de 0,0 para evitar erros, definindo fase como 0.
            if I_component == 0 and Q_component == 0:
                estimated_phase_rad = 0
            else:
                estimated_phase_rad = np.arctan2(Q_component, I_component)

            # Garante que a fase esteja no intervalo [0, 2*pi).
            if estimated_phase_rad < 0:
                estimated_phase_rad += 2 * np.pi

            # Encontra o símbolo da constelação (no QAM8_DECODE_MAP_RAD) que está mais próximo
            # do símbolo recebido no plano I-Q (menor distância euclidiana).
            closest_symbol_bits = None
            min_distance = float('inf')

            for (ref_amp, ref_phase_rad), sym_bits in self.QAM8_DECODE_MAP_RAD.items():
                # Converte as referências de amplitude/fase para coordenadas I-Q.
                ref_I = ref_amp * np.cos(ref_phase_rad)
                ref_Q = ref_amp * np.sin(ref_phase_rad)

                # Calcula a distância euclidiana entre o ponto recebido (I, Q) e o ponto de referência (ref_I, ref_Q).
                distance = np.sqrt((I_component - ref_I)**2 + (Q_component - ref_Q)**2)

                if distance < min_distance:
                    min_distance = distance
                    closest_symbol_bits = sym_bits # Armazena os bits correspondentes ao símbolo mais próximo
            
            bits += closest_symbol_bits

        return bits


# --- Mapeamento de protocolos para uso no simulador ---
# Cria uma instância da classe ModulacoesPortadora para acessar seus métodos.
_modulacoes_portadora_instance = ModulacoesPortadora()

MODULACOES_PORTADORA_TX = {
    'ASK': _modulacoes_portadora_instance.ask,
    'FSK': _modulacoes_portadora_instance.fsk,
    '8-QAM': _modulacoes_portadora_instance.qam_8
}

MODULACOES_PORTADORA_RX = {
    'ASK': _modulacoes_portadora_instance.demodular_ask,
    'FSK': _modulacoes_portadora_instance.demodular_fsk,
    '8-QAM': _modulacoes_portadora_instance.demodular_qam_8
}