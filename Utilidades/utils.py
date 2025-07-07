import numpy as np
import matplotlib.pyplot as plt

def text_to_binary(text):
    """
    Converte uma string de texto para uma string contínua de bits em ASCII 8 bits.
    
    Args:
        text (str): Texto a ser convertido.
        
    Returns:
        str: String contendo os bits concatenados correspondentes aos caracteres ASCII.
    """
    return ''.join(format(ord(char), '08b') for char in text)

def binary_to_text(binary_str):
    """
    Converte uma string contínua de bits para texto ASCII.
    
    Args:
        binary_str (str): String de bits concatenados.
        
    Returns:
        str: Texto correspondente aos bytes de 8 bits, ignorando bytes nulos.
    """
    # Ajusta a string para múltiplos de 8 bits para evitar erros na conversão
    padding = len(binary_str) % 8
    if padding != 0:
        binary_str = binary_str[:len(binary_str) - padding]  # Remove bits extras do final

    # Divide a string em blocos de 8 bits (1 byte)
    chars = [binary_str[i:i+8] for i in range(0, len(binary_str), 8)]
    
    # Converte cada byte para caractere ASCII, ignorando bytes com valor 0 (nulos)
    return ''.join(chr(int(char, 2)) for char in chars if int(char, 2) != 0)

def plot_signal(time_or_x, signal, title, xlabel="Tempo (s)", ylabel="Amplitude (V)", is_digital=False):
    """
    Plota um sinal, seja digital ou analógico, em um gráfico claro e ajustado.
    
    Args:
        time_or_x (array-like): Eixo horizontal (tempo ou índice).
        signal (array-like): Valores do sinal a serem plotados.
        title (str): Título do gráfico.
        xlabel (str, opcional): Rótulo do eixo X. Default é "Tempo (s)".
        ylabel (str, opcional): Rótulo do eixo Y. Default é "Amplitude (V)".
        is_digital (bool, opcional): Se True, usa passo para visualizar sinais digitais. Default é False.
    """
    plt.figure(figsize=(15, 4))
    
    if is_digital:
        # Para sinais digitais, usa 'steps-post' para o efeito de blocos
        plt.step(time_or_x, signal, where='post')
    else:
        plt.plot(time_or_x, signal)
    
    plt.title(title, fontsize=14)
    plt.xlabel(xlabel, fontsize=12)
    plt.ylabel(ylabel, fontsize=12)
    plt.grid(True)
    
    # Ajusta limites do eixo Y com margem para melhor visualização
    min_val = np.min(signal)
    max_val = np.max(signal)
    plt.ylim(min_val - abs(min_val)*0.2 - 0.2, max_val + abs(max_val)*0.2 + 0.2)
    
    plt.tight_layout()
    plt.show()

def plot_constellation(qam_points, title="Diagrama de Constelação 8-QAM"):
    """
    Plota o diagrama de constelação para modulações QAM, mostrando pontos no plano I-Q.
    
    Args:
        qam_points (list ou array): Lista de números complexos representando pontos na constelação.
        title (str, opcional): Título do gráfico.
    """
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
    
    # Anota os pontos para facilitar a identificação
    for i, point in enumerate(qam_points):
        plt.annotate(f'S{i}', (point.real, point.imag))
        
    plt.tight_layout()
    plt.show()
