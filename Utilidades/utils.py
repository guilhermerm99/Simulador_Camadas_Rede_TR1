# Utilidades/utils.py

import numpy as np
import matplotlib.pyplot as plt

def text_to_binary(text):
    """Converte uma string de texto para uma string contínua de bits (usando ASCII de 8 bits)."""
    return ''.join(format(ord(char), '08b') for char in text)

def binary_to_text(binary_str):
    """Converte uma string contínua de bits de volta para texto."""
    # Garante que a string seja múltipla de 8 para evitar erros
    padding = len(binary_str) % 8
    if padding != 0:
        binary_str = binary_str[:len(binary_str) - padding] # Remove padding se houver

    chars = [binary_str[i:i+8] for i in range(0, len(binary_str), 8)]
    # Ignora caracteres nulos que possam surgir de blocos incompletos
    return ''.join(chr(int(char, 2)) for char in chars if int(char, 2) != 0)

def plot_signal(time_or_x, signal, title, xlabel="Tempo (s)", ylabel="Amplitude (V)", is_digital=False):
    """
    Função genérica para plotar sinais digitais ou analógicos.
    """
    plt.figure(figsize=(15, 4))
    if is_digital:
        # 'steps-post' cria o visual de blocos para sinais digitais
        plt.step(time_or_x, signal, where='post')
    else:
        plt.plot(time_or_x, signal)
    
    plt.title(title, fontsize=14)
    plt.xlabel(xlabel, fontsize=12)
    plt.ylabel(ylabel, fontsize=12)
    plt.grid(True)
    # Ajusta os limites para melhor visualização
    min_val = np.min(signal)
    max_val = np.max(signal)
    plt.ylim(min_val - abs(min_val*0.2) - 0.2, max_val + abs(max_val*0.2) + 0.2)
    plt.tight_layout()
    plt.show()

def plot_constellation(qam_points, title="Diagrama de Constelação 8-QAM"):
    """Plota o diagrama de constelação para modulações de quadratura."""
    # Extrai as partes Real (I) e Imaginária (Q)
    i_components = [p.real for p in qam_points]
    q_components = [p.imag for p in qam_points]
    
    plt.figure(figsize=(6, 6))
    plt.scatter(i_components, q_components, c='blue', marker='o')
    
    plt.title(title, fontsize=14)
    plt.xlabel("Componente em Fase (I)", fontsize=12)
    plt.ylabel("Componente em Quadratura (Q)", fontsize=12)
    plt.grid(True)
    plt.axhline(0, color='black', linewidth=0.5)
    plt.axvline(0, color='black', linewidth=0.5)
    
    # Adiciona anotações para os pontos (opcional, mas didático)
    for i, point in enumerate(qam_points):
        plt.annotate(f'S{i}', (point.real, point.imag))
        
    plt.tight_layout()
    plt.show()