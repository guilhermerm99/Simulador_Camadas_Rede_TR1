import numpy as np
import matplotlib.pyplot as plt

def text_to_binary(text):
    """
    Converte uma string de texto para uma sequência contínua de bits,
    utilizando a codificação ASCII de 8 bits para cada caractere.
    
    Args:
        text (str): O texto de entrada a ser convertido.
        
    Returns:
        str: Uma string contendo os bits concatenados (ex: "0100100001100101...").
    """
    # Para cada caractere no texto, obtém seu valor ASCII (ord()) e o formata
    # como uma string binária de 8 bits, preenchendo com zeros à esquerda se necessário.
    # Esta é uma operação fundamental na Camada de Aplicação/Apresentação para preparar os dados.
    return ''.join(format(ord(char), '08b') for char in text)

def binary_to_text(binary_str):
    """
    Converte uma string contínua de bits de volta para texto ASCII.
    Assume que a string de bits representa caracteres ASCII de 8 bits.
    
    Args:
        binary_str (str): A string de bits concatenados a ser convertida.
        
    Returns:
        str: O texto correspondente aos bytes decodificados.
    """
    # Ajusta o comprimento da string binária para ser um múltiplo de 8 bits (um byte).
    # Isso é crucial para evitar erros de conversão caso a string não esteja completa no final,
    # garantindo que apenas bytes completos sejam processados.
    padding = len(binary_str) % 8
    if padding != 0:
        binary_str = binary_str[:len(binary_str) - padding]  # Remove bits extras do final.

    # Divide a string binária em blocos de 8 bits, cada um representando um byte.
    chars = [binary_str[i:i+8] for i in range(0, len(binary_str), 8)]
    
    # Converte cada byte binário de volta para seu caractere ASCII correspondente.
    # Ignora bytes que representam o valor nulo (0), que não são caracteres de texto imprimíveis.
    # Esta é a etapa final de decodificação na Camada de Aplicação/Apresentação.
    return ''.join(chr(int(char, 2)) for char in chars if int(char, 2) != 0)

def plot_signal(time_or_x, signal, title, xlabel="Tempo (s)", ylabel="Amplitude (V)", is_digital=False):
    """
    Plota um sinal genérico (digital ou analógico) em um gráfico.
    Esta função é utilizada para visualizar os sinais em diferentes estágios das camadas Física e de Enlace.
    Ajusta a visualização para clareza e proporção.
    
    Args:
        time_or_x (array-like): Os valores para o eixo horizontal (e.g., tempo, índice de amostra).
        signal (array-like): Os valores do sinal a serem plotados.
        title (str): O título do gráfico.
        xlabel (str, opcional): O rótulo do eixo X. Padrão é "Tempo (s)".
        ylabel (str, opcional): O rótulo do eixo Y. Padrão é "Amplitude (V)".
        is_digital (bool, opcional): Se True, o sinal é plotado como degraus (para sinais digitais, Camada Física - Banda Base).
                                      Se False, é plotado como uma linha contínua (para sinais analógicos, Camada Física - Passa-faixa).
    """
    plt.figure(figsize=(15, 4)) # Cria uma nova figura com tamanho especificado para o gráfico.
    
    if is_digital:
        # Para sinais digitais (e.g., codificação de linha), usa plt.step com 'where='post'' para criar uma plotagem em degraus,
        # onde a transição ocorre após o ponto de tempo, representando a mudança de nível lógico.
        plt.step(time_or_x, signal, where='post')
    else:
        # Para sinais analógicos (e.g., sinal modulado por portadora), usa plt.plot para uma linha contínua,
        # representando a variação contínua da amplitude/fase/frequência.
        plt.plot(time_or_x, signal)
    
    plt.title(title, fontsize=14) # Define o título do gráfico.
    plt.xlabel(xlabel, fontsize=12) # Define o rótulo do eixo X.
    plt.ylabel(ylabel, fontsize=12) # Define o rótulo do eixo Y.
    plt.grid(True) # Adiciona uma grade ao gráfico para facilitar a leitura.
    
    # Ajusta os limites do eixo Y para garantir que o sinal seja totalmente visível,
    # com uma pequena margem acima e abaixo dos valores mínimo e máximo do sinal.
    min_val = np.min(signal)
    max_val = np.max(signal)
    plt.ylim(min_val - abs(min_val)*0.2 - 0.2, max_val + abs(max_val)*0.2 + 0.2)
    
    plt.tight_layout() # Ajusta automaticamente os parâmetros da plotagem para um layout apertado, otimizando o espaço.
    plt.show() # Exibe a figura do gráfico.

def plot_constellation(qam_points, title="Diagrama de Constelação 8-QAM"):
    """
    Plota o diagrama de constelação para modulações QAM (Camada Física), mostrando os pontos
    no plano I-Q (Em Fase vs. Quadratura). Cada ponto representa um símbolo transmitido.
    
    Args:
        qam_points (list ou array): Uma lista de números complexos, onde a parte real
                                     é a componente Em Fase (I) e a parte imaginária
                                     é a componente em Quadratura (Q) de cada símbolo.
        title (str, opcional): O título do gráfico. Padrão é "Diagrama de Constelação 8-QAM".
    """
    # Extrai as componentes Em Fase (I) e em Quadratura (Q) dos pontos complexos.
    # A componente I representa o eixo horizontal e a Q o vertical no diagrama de constelação.
    i_components = [p.real for p in qam_points]
    q_components = [p.imag for p in qam_points]
    
    plt.figure(figsize=(6, 6)) # Cria uma nova figura quadrada para a constelação.
    # Plota os pontos da constelação como um scatter plot. Cada ponto é um símbolo modulado.
    plt.scatter(i_components, q_components, c='blue', marker='o')
    
    plt.title(title, fontsize=14) # Define o título do gráfico.
    plt.xlabel("Componente em Fase (I)", fontsize=12) # Rótulo do eixo X.
    plt.ylabel("Componente em Quadratura (Q)", fontsize=12) # Rótulo do eixo Y.
    plt.grid(True) # Adiciona uma grade.
    plt.axhline(0, color='black', linewidth=0.5) # Desenha uma linha horizontal no zero (eixo I).
    plt.axvline(0, color='black', linewidth=0.5) # Desenha uma linha vertical no zero (eixo Q).
    plt.axis('equal') # Garante que as escalas dos eixos X e Y sejam idênticas, para uma representação correta da constelação.
    
    # Anota cada ponto da constelação com um identificador (e.g., S0, S1), representando o símbolo correspondente.
    # A posição da anotação é ligeiramente deslocada para evitar sobrepor o ponto.
    for i, point in enumerate(qam_points):
        plt.annotate(f'S{i}', (point.real + 0.05, point.imag + 0.05)) 
        
    plt.tight_layout() # Ajusta automaticamente os parâmetros da plotagem para um layout apertado.
    plt.show() # Exibe a figura do diagrama de constelação.