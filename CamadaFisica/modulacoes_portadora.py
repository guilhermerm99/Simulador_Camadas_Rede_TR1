# CamadaFisica/modulacoes_portadora.py
import numpy as np

# Constantes para simulação (ajustáveis para visualização)
FS_PORTADORA = 1000
TEMPO_SIMBOLO = 0.05 # Duração de um símbolo em segundos

# --- FUNÇÃO _gerar_portadora REFATORADA ---
# Removendo o valor padrão para 'fase' na assinatura, forçando a passagem explícita
def _gerar_portadora(frequencia, amplitude, duracao_simbolo, fase):
    """Auxiliar: Gera uma senoide para a portadora com fase explícita."""
    t = np.linspace(0, duracao_simbolo, int(FS_PORTADORA * duracao_simbolo), endpoint=False)
    return amplitude * np.sin(2 * np.pi * frequencia * t + fase)

# As funções ask e fsk não usam 'phase', então não precisam de alteração nelas,
# mas se elas chamassem _gerar_portadora sem fase, teriam que passar fase=0.
# No nosso código atual, ASK e FSK chamam _gerar_portadora com 3 argumentos, e a fase é ignorada ou não utilizada na chamada.
# Mas na verdade, ask e fsk *estão* chamando _gerar_portadora com 3 argumentos, e qam_8 com 4.
# O problema é que a assinatura anterior com fase=0 permitia ambos.
# Agora, todas as chamadas a _gerar_portadora *terão* que passar o argumento 'fase'.

# Ajustando ask e fsk para passar 'fase=0' explicitamente
def ask(bits: str) -> list[float]:
    signal = []
    fc = 50
    for bit in bits:
        if bit == '1':
            signal.extend(_gerar_portadora(fc, 1.0, TEMPO_SIMBOLO, fase=0)) # Passa fase=0 explicitamente
        elif bit == '0':
            signal.extend(_gerar_portadora(fc, 0.0, TEMPO_SIMBOLO, fase=0)) # Passa fase=0 explicitamente
        else:
            raise ValueError("Bits devem ser '0' ou '1'")
    return signal

def fsk(bits: str) -> list[float]:
    signal = []
    f0 = 20
    f1 = 40
    for bit in bits:
        if bit == '1':
            signal.extend(_gerar_portadora(f1, 1.0, TEMPO_SIMBOLO, fase=0)) # Passa fase=0 explicitamente
        elif bit == '0':
            signal.extend(_gerar_portadora(f0, 1.0, TEMPO_SIMBOLO, fase=0)) # Passa fase=0 explicitamente
        else:
            raise ValueError("Bits devem ser '0' ou '1'")
    return signal

def qam_8(bits: str) -> list[float]:
    if len(bits) % 3 != 0:
        bits = bits.ljust((len(bits) + 2) // 3 * 3, '0')

    signal = []
    fc = 50
    symbol_map = {
        '000': (0.707, 0),
        '001': (0.707, 45),
        '010': (0.707, 90),
        '011': (0.707, 135),
        '100': (1.0, 180),
        '101': (1.0, 225),
        '110': (1.0, 270),
        '111': (1.0, 315)
    }

    for i in range(0, len(bits), 3):
        symbol_bits = bits[i:i+3]
        amplitude, phase_deg = symbol_map.get(symbol_bits, (0, 0))
        phase_rad = np.deg2rad(phase_deg)
        signal.extend(_gerar_portadora(fc, amplitude, TEMPO_SIMBOLO, fase=phase_rad)) # Fase já é passada aqui
    return signal


# --- As funções de demodulação não precisam de alteração ---
def demodular_ask(signal: list[float]) -> str:
    bits = ""
    amostras_por_simbolo = int(FS_PORTADORA * TEMPO_SIMBOLO)
    for i in range(0, len(signal), amostras_por_simbolo):
        segment = signal[i:i + amostras_por_simbolo]
        if not segment: continue
        avg_amplitude = np.mean(np.abs(segment))

        if avg_amplitude > 0.5:
            bits += '1'
        else:
            bits += '0'
    return bits

def demodular_fsk(signal: list[float]) -> str:
    bits = ""
    amostras_por_simbolo = int(FS_PORTADORA * TEMPO_SIMBOLO)
    f0 = 20
    f1 = 40

    for i in range(0, len(signal), amostras_por_simbolo):
        segment = np.array(signal[i:i + amostras_por_simbolo])
        if len(segment) < amostras_por_simbolo:
            continue

        t = np.linspace(0, TEMPO_SIMBOLO, amostras_por_simbolo, endpoint=False)
        sin_f0 = np.sin(2 * np.pi * f0 * t)
        sin_f1 = np.sin(2 * np.pi * f1 * t)

        corr_f0 = np.sum(segment * sin_f0)
        corr_f1 = np.sum(segment * sin_f1)

        if corr_f1 > corr_f0:
            bits += '1'
        else:
            bits += '0'
    return bits

def demodular_qam_8(signal: list[float]) -> str:
    bits = ""
    amostras_por_simbolo = int(FS_PORTADORA * TEMPO_SIMBOLO)
    fc = 50

    symbol_decode_map = {
        (0.707, 0): '000',
        (0.707, 45): '001',
        (0.707, 90): '010',
        (0.707, 135): '011',
        (1.0, 180): '100',
        (1.0, 225): '101',
        (1.0, 270): '110',
        (1.0, 315): '111'
    }

    symbol_decode_map_rad = {}
    for (amp, phase_deg), sym_bits in symbol_decode_map.items():
        symbol_decode_map_rad[(amp, np.deg2rad(phase_deg))] = sym_bits


    for i in range(0, len(signal), amostras_por_simbolo):
        segment = np.array(signal[i:i + amostras_por_simbolo])
        if len(segment) < amostras_por_simbolo:
            continue

        t = np.linspace(0, TEMPO_SIMBOLO, amostras_por_simbolo, endpoint=False)
        carrier_cos = np.cos(2 * np.pi * fc * t)
        carrier_sin = np.sin(2 * np.pi * fc * t)

        I_component = 2 * np.mean(segment * carrier_cos)
        Q_component = 2 * np.mean(segment * carrier_sin)

        estimated_amplitude = np.sqrt(I_component**2 + Q_component**2)
        if I_component == 0 and Q_component == 0:
             estimated_phase_rad = 0
        else:
             estimated_phase_rad = np.arctan2(Q_component, I_component)

        if estimated_phase_rad < 0:
            estimated_phase_rad += 2 * np.pi

        closest_symbol = None
        min_distance = float('inf')

        for (ref_amp, ref_phase_rad), sym_bits in symbol_decode_map_rad.items():
            ref_I = ref_amp * np.cos(ref_phase_rad)
            ref_Q = ref_amp * np.sin(ref_phase_rad)

            distance = np.sqrt((I_component - ref_I)**2 + (Q_component - ref_Q)**2)

            if distance < min_distance:
                min_distance = distance
                closest_symbol = sym_bits
        
        bits += closest_symbol

    return bits


# Mapeamento para uso no simulador
MODULACOES_PORTADORA_TX = {
    'ASK': ask,
    'FSK': fsk,
    '8-QAM': qam_8
}

MODULACOES_PORTADORA_RX = {
    'ASK': demodular_ask,
    'FSK': demodular_fsk,
    '8-QAM': demodular_qam_8
}