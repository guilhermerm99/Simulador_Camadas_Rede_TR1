# CamadaFisica/modulacoes_digitais.py
import numpy as np

def nrz_polar(bits: str) -> list[float]:
    """
    Simula a modulação Non-return to Zero Polar (NRZ-Polar).
    Representa '1' como nível alto (+V) e '0' como nível baixo (-V).
    Para fins de visualização, usamos 1 e -1.
    """
    signal = []
    for bit in bits:
        if bit == '1':
            signal.append(1.0)
        elif bit == '0':
            signal.append(-1.0)
        else:
            raise ValueError("Bits devem ser '0' ou '1'")
    return signal

def manchester(bits: str) -> list[float]:
    """
    Simula a modulação Manchester.
    '0' -> transição de alto para baixo (1 para -1) no meio do bit.
    '1' -> transição de baixo para alto (-1 para 1) no meio do bit.
    Cada bit ocupa 2 unidades de tempo para a visualização.
    """
    signal = []
    for bit in bits:
        if bit == '1':
            signal.extend([-1.0, 1.0])  # Transição de baixo para alto
        elif bit == '0':
            signal.extend([1.0, -1.0])   # Transição de alto para baixo
        else:
            raise ValueError("Bits devem ser '0' ou '1'")
    return signal

def bipolar(bits: str) -> list[float]:
    """
    Simula a modulação Bipolar (AMI - Alternate Mark Inversion).
    '0' -> nível zero (0V).
    '1' -> alternam entre +V e -V.
    """
    signal = []
    last_one_voltage = 1.0  # Inicia com +V para o primeiro '1'
    for bit in bits:
        if bit == '0':
            signal.append(0.0)
        elif bit == '1':
            signal.append(last_one_voltage)
            last_one_voltage *= -1.0  # Alterna para o próximo '1'
        else:
            raise ValueError("Bits devem ser '0' ou '1'")
    return signal

def decodificar_nrz_polar(signal: list[float]) -> str:
    """Decodifica sinal NRZ-Polar de volta para bits."""
    bits = ""
    for val in signal:
        if val >= 0: # Considerando um pequeno limiar para flutuações, mas simples aqui
            bits += '1'
        else:
            bits += '0'
    return bits

def decodificar_manchester(signal: list[float]) -> str:
    """Decodifica sinal Manchester de volta para bits."""
    bits = ""
    # Assume que cada bit ocupa 2 amostras
    for i in range(0, len(signal), 2):
        if i + 1 < len(signal):
            # Transição de -1 para 1 significa '1'
            if signal[i] < signal[i+1]: # -1 para 1
                bits += '1'
            # Transição de 1 para -1 significa '0'
            elif signal[i] > signal[i+1]: # 1 para -1
                bits += '0'
            else:
                # Caso onde não há transição significativa (erro ou padding)
                # Para fins de simulação, pode-se decidir como tratar.
                # Aqui, assumimos que 0 ou 1 é determinado pela primeira metade do bit
                # ou por algum critério de erro. Simplesmente evitamos falha para bits incompletos
                pass
        else:
            pass # Sinal incompleto

    return bits

def decodificar_bipolar(signal: list[float]) -> str:
    """Decodifica sinal Bipolar de volta para bits."""
    bits = ""
    for val in signal:
        if val == 0:
            bits += '0'
        else:
            bits += '1' # Não importa se é +V ou -V, um pulso diferente de zero é '1'
    return bits

# Mapeamento para uso no simulador
MODULACOES_DIGITAIS_TX = {
    'NRZ-Polar': nrz_polar,
    'Manchester': manchester,
    'Bipolar': bipolar
}

MODULACOES_DIGITAIS_RX = {
    'NRZ-Polar': decodificar_nrz_polar,
    'Manchester': decodificar_manchester,
    'Bipolar': decodificar_bipolar
}