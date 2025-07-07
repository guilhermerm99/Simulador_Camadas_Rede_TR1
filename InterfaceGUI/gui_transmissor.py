import tkinter as tk
from tkinter import ttk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import numpy as np
import threading
import queue
import sys

# Adiciona o diretório pai ao caminho de busca de módulos para permitir importações locais.
# Essencial para acessar módulos como 'transmissor' e 'utils' que estão fora do diretório atual.
sys.path.append('../')

# Importa os módulos do simulador e utilitários necessários para a lógica de transmissão.
from Simulador import transmissor
from Utilidades import utils # Importa utils para usar as funções de conversão de texto/binário.

class TransmissorGUI(ttk.Frame):
    """
    Interface Gráfica do Utilizador (GUI) para o Transmissor do simulador de camadas de rede.
    Esta classe permite configurar os parâmetros de transmissão (enquadramento, modulação,
    detecção/correção de erro), visualizar os sinais gerados em diferentes etapas e
    iniciar o processo de envio de dados para o recetor.
    """
    def __init__(self, master):
        """
        Inicializa a GUI do Transmissor, configurando a janela principal e os seus componentes.
        
        Args:
            master (tk.Tk): A janela principal do Tkinter à qual este frame será anexado.
        """
        super().__init__(master, padding="10")
        self.master = master
        self.master.title("Simulador de Transmissão - Transmissor (Tx)") # Define o título da janela.
        self.master.geometry("1200x800")  # Define o tamanho inicial da janela para uma boa visualização.
        self.pack(fill=tk.BOTH, expand=True) # Empacota o frame para preencher todo o espaço da janela.

        # Fila para comunicação segura entre threads: permite que a thread de transmissão (backend)
        # envie atualizações para a thread principal da GUI sem causar bloqueios ou instabilidade.
        self.update_queue = queue.Queue()

        # Variáveis de controlo do Tkinter para os widgets de configuração na GUI.
        self.msg_var = tk.StringVar(value="00000") # Variável para a mensagem a ser transmitida (valor padrão para teste).
        self.raw_binary_input = tk.BooleanVar(value=True) # Controla se a entrada é binário puro ou texto para conversão.
        
        # Variáveis para os tipos de enquadramento (Camada de Enlace) e modulação (Camada Física),
        # com valores padrão que representam opções realistas para iniciar a simulação.
        self.enquadramento_var = tk.StringVar(value='Bit Stuffing (Flags)') 
        self.mod_digital_var = tk.StringVar(value='NRZ-Polar')
        # Alteração: Definindo 'Nenhum' como valor padrão para a modulação por portadora.
        self.mod_portadora_var = tk.StringVar(value='Nenhum') 
        self.detecao_erro_var = tk.StringVar(value='CRC-32') # Variável para o tipo de deteção de erro (Camada de Enlace).
        self.correcao_erro_var = tk.StringVar(value='Hamming') # Variável para o tipo de correção de erro (Camada de Enlace).
        self.taxa_erros_var = tk.DoubleVar(value=0.01) # Variável para a taxa de erros no canal (valor decimal entre 0 e 1).

        # Chama o método para criar e posicionar todos os widgets na interface.
        self._create_widgets()
        # Inicia o processamento periódico da fila de atualizações da GUI.
        # Esta função será chamada repetidamente pela thread principal do Tkinter para manter a GUI atualizada.
        self.process_queue()

    def _create_widgets(self):
        """
        Constrói a estrutura visual da GUI, organizando os painéis, frames e widgets
        de entrada/saída de informações e os contentores para os gráficos.
        """
        # Configura o layout de grelha para a janela principal, dividindo-a em duas colunas.
        self.grid_columnconfigure(0, weight=1, minsize=450)  # Coluna esquerda para configurações, com largura mínima.
        self.grid_columnconfigure(1, weight=3)  # Coluna direita para gráficos, ocupando mais espaço.
        self.grid_rowconfigure(0, weight=1) # A única linha expande-se verticalmente.

        # Painel esquerdo: Contém os frames para configurações e status da transmissão.
        left_panel = ttk.Frame(self)
        left_panel.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

        # Frame para as opções de configuração da simulação.
        config_frame = ttk.LabelFrame(left_panel, text="Configurações da Simulação", padding="10")
        config_frame.pack(fill=tk.X, pady=5) # Empacota para preencher a largura do painel esquerdo.
        config_frame.grid_columnconfigure(1, weight=1) # Permite que a coluna dos valores se expanda.
        config_frame.grid_columnconfigure(2, weight=1) # Coluna extra para o checkbox de binário puro.

        # Listas de opções para os Comboboxes, representando as escolhas para cada camada.
        enquadramento_options = ["Contagem de caracteres", "Byte Stuffing (Flags)", "Bit Stuffing (Flags)"]
        detecao_erro_options = ["Nenhum", "Paridade Par", "CRC-32"] 
        correcao_erro_options = ["Nenhum", "Hamming"] 
        mod_digital_options = ["NRZ-Polar", "Manchester", "Bipolar"] # Codificações de linha (Camada Física - Banda Base).
        # Alteração: Adicionando 'Nenhum' às opções de modulação por portadora.
        mod_portadora_options = ["Nenhum", "ASK", "FSK", "8-QAM"] # Modulações de portadora (Camada Física - Passa-faixa).

        # Criação das linhas de controlo para cada parâmetro de configuração, incluindo rótulos e widgets de entrada.
        self.create_control_row(config_frame, 0, "Mensagem:", ttk.Entry(config_frame, textvariable=self.msg_var))
        # Checkbox para alternar entre entrada de texto (para conversão ASCII) e binário puro.
        ttk.Checkbutton(config_frame, text="Entrada Binária Pura (0s e 1s)", variable=self.raw_binary_input).grid(row=0, column=2, sticky="w", padx=5, pady=2)

        # Configurações da Camada de Enlace.
        self.create_control_row(config_frame, 1, "Enquadramento:", ttk.Combobox(config_frame, textvariable=self.enquadramento_var, values=enquadramento_options, state="readonly"))
        # Configurações da Camada Física (Banda Base).
        self.create_control_row(config_frame, 2, "Mod. Digital:", ttk.Combobox(config_frame, textvariable=self.mod_digital_var, values=mod_digital_options, state="readonly"))
        # Configurações da Camada Física (Passa-faixa).
        self.create_control_row(config_frame, 3, "Mod. Portadora:", ttk.Combobox(config_frame, textvariable=self.mod_portadora_var, values=mod_portadora_options, state="readonly"))
        # Configurações de Detecção e Correção de Erro (Camada de Enlace).
        self.create_control_row(config_frame, 4, "Deteção de Erro:", ttk.Combobox(config_frame, textvariable=self.detecao_erro_var, values=detecao_erro_options, state="readonly"))
        self.create_control_row(config_frame, 5, "Correção de Erro:", ttk.Combobox(config_frame, textvariable=self.correcao_erro_var, values=correcao_erro_options, state="readonly"))

        # Configuração do slider para a taxa de erros no canal, com rótulo de valor dinâmico.
        # Simula a introdução de ruído ou interferência no canal de transmissão.
        ttk.Label(config_frame, text="Taxa de Erros no Canal:").grid(row=6, column=0, sticky="w", padx=5, pady=(10,0))
        error_scale = ttk.Scale(config_frame, from_=0.0, to_=0.1, orient=tk.HORIZONTAL,
                                 variable=self.taxa_erros_var, command=lambda v: self.error_label.config(text=f"{float(v):.3f}"))
        error_scale.grid(row=7, column=0, columnspan=2, sticky="ew", padx=5)
        self.error_label = ttk.Label(config_frame, text=f"{self.taxa_erros_var.get():.3f}")
        self.error_label.grid(row=8, column=0, columnspan=2, sticky="w", padx=5)

        # Botão para iniciar o processo de transmissão.
        self.send_button = ttk.Button(left_panel, text="Iniciar Transmissão", command=self.start_transmission_thread)
        self.send_button.pack(fill=tk.X, pady=20)

        # Frame para exibir o status atual da transmissão.
        status_frame = ttk.LabelFrame(left_panel, text="Estado", padding=10)
        status_frame.pack(fill=tk.BOTH, expand=True)
        self.status_label = ttk.Label(status_frame, text="Pronto.", foreground="blue", wraplength=400)
        self.status_label.pack(fill=tk.BOTH, expand=True)

        # Painel direito para exibir os gráficos dos sinais gerados nas diferentes etapas do transmissor.
        plot_container = ttk.LabelFrame(self, text="Gráficos do Sinal Transmitido", padding="10")
        plot_container.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")

        # Notebook (abas) para organizar os diferentes gráficos de sinal.
        self.plot_notebook = ttk.Notebook(plot_container)
        self.plot_notebook.pack(fill=tk.BOTH, expand=True)

        # Criação das abas de gráficos: Sinal Digital (banda base), Sinal Modulado (passa-faixa) e Constelação 8-QAM.
        # Cada aba inclui um gráfico Matplotlib com sua própria barra de ferramentas de navegação.
        self.ax_digital, self.canvas_digital, self.toolbar_digital = self.create_plot_tab("Sinal Digital", figsize=(10, 4.5))
        self.ax_analog, self.canvas_analog, self.toolbar_analog = self.create_plot_tab("Sinal Modulado", figsize=(10, 4.5))
        self.ax_const, self.canvas_const, self.toolbar_const = self.create_plot_tab("Constelação 8-QAM (TX)", figsize=(8, 6))

    def create_control_row(self, parent, row, label_text, widget):
        """
        Cria uma linha de controlo genérica com um rótulo e um widget de entrada/seleção
        dentro de um frame pai.
        
        Args:
            parent (ttk.Frame): O frame pai onde a linha será adicionada.
            row (int): O número da linha na grelha do frame pai.
            label_text (str): O texto do rótulo a ser exibido.
            widget (ttk.Widget): O widget de entrada (e.g., ttk.Entry, ttk.Combobox) a ser posicionado.
        """
        ttk.Label(parent, text=label_text).grid(row=row, column=0, sticky="w", padx=5, pady=2)
        widget.grid(row=row, column=1, sticky="ew", padx=5, pady=2)

    def create_plot_tab(self, tab_name, figsize=(8, 3.5)):
        """
        Cria uma nova aba no notebook de gráficos, configurando uma figura Matplotlib,
        o seu canvas Tkinter e a barra de ferramentas de navegação associada.
        
        Args:
            tab_name (str): O nome que será exibido na aba e como título inicial do gráfico.
            figsize (tuple): O tamanho da figura Matplotlib (largura, altura em polegadas).
            
        Returns:
            tuple: Uma tupla contendo o objeto 'Axes' do Matplotlib, o 'FigureCanvasTkAgg' do Tkinter e a 'NavigationToolbar2Tk'.
        """
        tab = ttk.Frame(self.plot_notebook) # Cria um novo frame que servirá como o conteúdo da aba.
        self.plot_notebook.add(tab, text=tab_name) # Adiciona este frame como uma nova aba ao notebook.
        fig, ax = plt.subplots(figsize=figsize) # Cria uma nova figura e um conjunto de eixos para o gráfico.
        fig.tight_layout(pad=2.5) # Ajusta o layout da figura para evitar sobreposições de elementos.
        canvas = FigureCanvasTkAgg(fig, master=tab) # Integra a figura Matplotlib ao ambiente Tkinter.
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True) # Empacota o widget do canvas para preencher a aba.

        toolbar = NavigationToolbar2Tk(canvas, tab) # Cria a barra de ferramentas padrão do Matplotlib (zoom, pan, guardar).
        toolbar.update() # Garante que a barra de ferramentas seja renderizada corretamente.
        canvas._tkcanvas.pack(fill=tk.BOTH, expand=True) # Empacota o widget do canvas novamente (necessário para a barra de ferramentas).

        self.clear_plot_ax(ax, canvas, title=tab_name) # Limpa o eixo e define o título inicial.
        return ax, canvas, toolbar

    def start_transmission_thread(self):
        """
        Inicia o processo de transmissão (lógica de backend) numa thread separada
        para não bloquear a GUI. Desabilita o botão de envio e limpa os gráficos
        antes de iniciar uma nova transmissão.
        """
        self.send_button.config(state="disabled") # Desabilita o botão para prevenir múltiplas transmissões simultâneas.
        self.clear_all() # Limpa todos os gráficos e status anteriores para uma nova simulação.

        message_input = self.msg_var.get() # Obtém a mensagem digitada pelo utilizador no campo de entrada.
        
        # Lógica para determinar se a entrada é uma string de bits pura (e.g., "01010") ou texto (e.g., "Olá").
        # Isso afeta a fase inicial de "codificação de fonte" (conversão para binário).
        if self.raw_binary_input.get():
            # Se a entrada é binário puro, valida se contém apenas os caracteres '0' e '1'.
            if not all(bit in '01' for bit in message_input):
                self.status_label.config(text="ERRO: Entrada binária pura deve conter apenas '0's e '1's.", foreground="red")
                self.send_button.config(state="normal") # Reabilita o botão em caso de erro de validação.
                return # Interrompe a função se a validação falhar.
            bits_to_send = message_input # Usa a string de entrada diretamente como a sequência de bits.
            original_message_for_log = message_input # A mensagem para logs e metadados é a própria string binária.
        else:
            # Se a entrada é texto, converte-a para uma sequência de bits ASCII (8 bits por caractere).
            bits_to_send = utils.text_to_binary(message_input)
            original_message_for_log = message_input # A mensagem para logs e metadados é o texto original.

        # Prepara o dicionário de parâmetros que será passado para a função de transmissão no backend.
        # Estes parâmetros definem o comportamento das camadas do simulador.
        params = {
            "message": original_message_for_log, # Mensagem original (texto ou binário puro) para os metadados.
            "bits_raw_input": bits_to_send, # A sequência de bits a ser processada pelas camadas do transmissor.
            "enquadramento_type": self.enquadramento_var.get(), # Tipo de enquadramento (Camada de Enlace).
            "mod_digital_type": self.mod_digital_var.get(), # Tipo de modulação digital (Camada Física - Banda Base).
            "mod_portadora_type": self.mod_portadora_var.get(), # Tipo de modulação de portadora (Camada Física - Passa-faixa).
            "detecao_erro_type": self.detecao_erro_var.get(), # Tipo de deteção de erro (Camada de Enlace).
            "correcao_erro_type": self.correcao_erro_var.get(), # Tipo de correção de erro (Camada de Enlace).
            "taxa_erros": self.taxa_erros_var.get() # Taxa de erros a ser simulada no canal.
        }

        # Cria e inicia uma nova thread para executar a função de transmissão (transmissor.run_transmitter).
        # Isso é fundamental para que a interface gráfica permaneça responsiva durante o processo de transmissão.
        thread = threading.Thread(target=transmissor.run_transmitter, args=(params, self.gui_update_callback))
        thread.daemon = True # Define a thread como "daemon" para que ela seja encerrada automaticamente
                             # quando o programa principal (a GUI) for fechado.
        thread.start() # Inicia a execução da thread.

    def gui_update_callback(self, update_dict):
        """
        Função de callback chamada pela thread de transmissão para enviar atualizações para a GUI.
        Esta função coloca as mensagens numa fila para processamento seguro na thread principal da GUI.
        
        Args:
            update_dict (dict): Dicionário contendo o tipo de atualização e os dados correspondentes.
        """
        self.update_queue.put(update_dict) # Adiciona o dicionário de atualização à fila.

    def process_queue(self):
        """
        Processa as mensagens na fila de atualização da GUI.
        Esta função é chamada periodicamente pela thread principal do Tkinter (`master.after()`).
        Garante que as atualizações da interface ocorram de forma segura e assíncrona.
        """
        try:
            while not self.update_queue.empty(): # Itera e processa todas as mensagens atualmente presentes na fila.
                msg = self.update_queue.get_nowait() # Obtém uma mensagem da fila sem bloquear a execução.
                msg_type = msg.get('type') # Extrai o tipo da mensagem para determinar a ação.

                # Direciona a mensagem para a função de atualização da GUI apropriada com base no seu tipo.
                if msg_type == 'status':
                    self.status_label.config(text=msg['message'], foreground=msg['color'])
                    # Reabilita o botão de envio se a transmissão foi concluída ou se ocorreu um erro.
                    if "concluída" in msg['message'] or "Erro" in msg['message']:
                        self.send_button.config(state="normal")
                elif msg_type == 'plot_digital':
                    self.update_digital_plot(msg['data']) # Atualiza o gráfico do sinal digital (Camada Física - Banda Base).
                elif msg_type == 'plot_analog':
                    self.update_analog_plot(msg['data']) # Atualiza o gráfico do sinal analógico modulado (Camada Física - Passa-faixa).
                elif msg_type == 'plot_constellation':
                    self.update_constellation_plot(msg['data']) # Atualiza o gráfico da constelação (para 8-QAM - Camada Física).
        finally:
            # Agenda a próxima chamada desta função após 100 milissegundos.
            # Isso cria um ciclo de eventos que mantém a GUI responsiva e processa as atualizações da fila.
            self.master.after(100, self.process_queue)

    def clear_all(self):
        """
        Limpa o conteúdo de todos os gráficos e os seus respetivos eixos,
        preparando a interface para uma nova simulação.
        """
        self.clear_plot_ax(self.ax_digital, self.canvas_digital, "Sinal Digital")
        self.clear_plot_ax(self.ax_analog, self.canvas_analog, "Sinal Modulado")
        self.clear_plot_ax(self.ax_const, self.canvas_const, "Constelação 8-QAM (TX)")

    def clear_plot_ax(self, ax, canvas, title):
        """
        Limpa o conteúdo de um conjunto de eixos Matplotlib e força o redesenho do canvas.
        
        Args:
            ax (matplotlib.axes.Axes): O objeto de eixos do Matplotlib a ser limpo.
            canvas (FigureCanvasTkAgg): O canvas Tkinter associado ao eixo.
            title (str): O título que será definido para o eixo após a limpeza.
        """
        ax.clear() # Remove todas as linhas, pontos, textos e configurações anteriores do eixo.
        ax.set_title(title, fontsize=12) # Define o título do eixo.
        ax.grid(True, linestyle='--', linewidth=0.5, alpha=0.8) # Adiciona uma grelha ao gráfico para facilitar a leitura.
        canvas.draw() # Força o redesenho do canvas para que as mudanças sejam visíveis na GUI.

    def update_digital_plot(self, plot_data):
        """
        Atualiza o gráfico que exibe o sinal digital gerado pela codificação de linha (Camada Física - Banda Base).
        Este sinal representa os bits após serem processados por técnicas como NRZ-Polar, Manchester ou Bipolar.
        
        Args:
            plot_data (dict): Dicionário contendo 't' (eixo de tempo), 'signal' (dados do sinal digital),
                              e 'config' (configurações da transmissão para o título e depuração).
        """
        ax, canvas = self.ax_digital, self.canvas_digital
        t, signal, config = plot_data['t'], plot_data['signal'], plot_data['config']
        
        # --- Secção de DEBUG para análise do sinal digital ---
        print(f"DEBUG: update_digital_plot - Tipo de Modulação Digital: {config['mod_digital_type']}")
        print(f"DEBUG: update_digital_plot - Comprimento do sinal: {len(signal)}")
        print(f"DEBUG: update_digital_plot - Primeiros 10 valores do sinal: {signal[:10]}")
        print(f"DEBUG: update_digital_plot - Últimos 10 valores do sinal: {signal[-10:]}")
        # Verifica se o sinal NRZ-Polar para '0's puros é uma linha plana em -1.0.
        if len(signal) > 0 and config['mod_digital_type'] == 'NRZ-Polar':
            unique_vals = np.unique(signal)
            print(f"DEBUG: update_digital_plot - Valores únicos no sinal: {unique_vals}")
            if len(unique_vals) == 1 and unique_vals[0] == -1.0:
                print("DEBUG: O array do sinal é plano em -1.0 como esperado para '0's em NRZ-Polar.")
            else:
                print("DEBUG: O array do sinal NÃO é plano em -1.0. Contém variações.")
        # --- Fim da Secção de DEBUG ---

        self.clear_plot_ax(ax, canvas, f"Sinal Digital ({config['mod_digital_type']})") # Limpa o gráfico e define o título.
        ax.step(t, signal, where='post', label=f"{config['mod_digital_type']}", color='dodgerblue') # Plota o sinal digital em degraus.
        ax.set_xlabel("Tempo (s)") # Define o rótulo do eixo X.
        ax.set_ylabel("Amplitude (V)") # Define o rótulo do eixo Y.
        if len(signal) > 0:
            # Ajusta os limites do eixo Y com uma margem dinâmica para melhor visualização do sinal.
            min_val = np.min(signal)
            max_val = np.max(signal)
            y_margin = (max_val - min_val) * 0.1 if (max_val - min_val) > 0 else 0.2
            ax.set_ylim(min_val - y_margin, max_val + y_margin)
            # Ajusta os limites do eixo X para começar em zero e ir até o final do sinal ou 1 segundo (para sinais muito longos).
            ax.set_xlim(left=0, right=max(t) if len(t) > 0 else 1)
        ax.legend() # Exibe a legenda do gráfico.
        canvas.draw() # Força o redesenho do canvas para atualizar o gráfico na GUI.

    def update_analog_plot(self, plot_data):
        """
        Atualiza o gráfico que exibe o sinal modulado (analógico) pronto para transmissão (Camada Física - Passa-faixa).
        Este sinal é o resultado da modulação da portadora (ASK, FSK, QAM) com o sinal digital.
        
        Args:
            plot_data (dict): Dicionário contendo 't' (eixo de tempo), 'signal' (dados do sinal),
                              e 'config' (configurações da transmissão para o título).
        """
        ax, canvas = self.ax_analog, self.canvas_analog
        t, signal, config = plot_data['t'], plot_data['signal'], plot_data['config']
        self.clear_plot_ax(ax, canvas, f"Sinal Modulado ({config['mod_portadora_type']})") # Limpa o gráfico e define o título.
        ax.plot(t, signal, label=f"{config['mod_portadora_type']}", color='coral') # Plota o sinal analógico como uma linha.
        ax.set_xlabel("Tempo (s)") # Rótulo do eixo X.
        ax.set_ylabel("Amplitude (V)") # Rótulo do eixo Y.

        window_duration = 2.5 # Define uma janela de visualização padrão de 2.5 segundos para o eixo X.
        max_time = t[-1] if len(t) > 0 else 0 # Obtém o tempo máximo do sinal.
        xlim_end = min(window_duration, max_time) # Define o limite final do eixo X (janela ou tempo total do sinal).
        ax.set_xlim(0, xlim_end) # Define os limites do eixo X.

        # Ajusta a margem vertical do gráfico para melhor visualização do sinal.
        if len(signal) > 0:
            margin = (max(signal) - min(signal)) * 0.1
            ax.set_ylim(min(signal) - margin, max(signal) + margin)

        ax.legend() # Exibe a legenda do gráfico.
        canvas.draw() # Força o redesenho do canvas.

    def update_constellation_plot(self, plot_data):
        """
        Atualiza o gráfico do diagrama de constelação para modulações como 8-QAM (Camada Física).
        Este gráfico representa os pontos no plano I/Q correspondentes aos símbolos transmitidos.
        
        Args:
            plot_data (dict): Dicionário contendo 'points' (lista de pontos complexos da constelação).
        """
        ax, canvas = self.ax_const, self.canvas_const
        points = plot_data['points']
        self.clear_plot_ax(ax, canvas, "Constelação 8-QAM (TX)") # Limpa o gráfico e define o título.
        real = [p.real for p in points] # Extrai as componentes em fase (I).
        imag = [p.imag for p in points] # Extrai as componentes em quadratura (Q).
        ax.scatter(real, imag, color='purple', s=40, alpha=0.8) # Plota os pontos da constelação.
        ax.axhline(0, color='gray', lw=0.5) # Desenha uma linha horizontal no zero.
        ax.axvline(0, color='gray', lw=0.5) # Desenha uma linha vertical no zero.
        ax.set_xlabel("Em Fase (I)") # Rótulo do eixo X.
        ax.set_ylabel("Quadratura (Q)") # Rótulo do eixo Y.
        
        # Ajusta os limites dos eixos para garantir que todos os pontos e a origem (0,0) sejam visíveis,
        # com uma margem extra para melhor visualização.
        all_coords = real + imag
        if all_coords:
            max_abs_val = max(abs(val) for val in all_coords)
            limit = max_abs_val * 1.2 # Adiciona 20% de margem.
            ax.set_xlim(-limit, limit)
            ax.set_ylim(-limit, limit)
        else: # Caso não haja pontos (e.g., no início da simulação ou se a modulação não for QAM).
            ax.set_xlim(-1.5, 1.5)
            ax.set_ylim(-1.5, 1.5)

        ax.set_aspect('equal', 'box') # Garante que os eixos tenham a mesma escala para uma representação fiel.
        
        # Anota cada ponto da constelação com um identificador (e.g., S0, S1...).
        # A posição da anotação é ligeiramente deslocada para evitar sobrepor o ponto visualmente.
        for i, point in enumerate(points):
            ax.annotate(f'S{i}', (point.real + 0.05, point.imag + 0.05), fontsize=8)
            
        canvas.draw() # Força o redesenho do canvas para atualizar o gráfico na GUI.

if __name__ == '__main__':
    root = tk.Tk() # Cria a janela principal do Tkinter.
    app = TransmissorGUI(root) # Instancia a aplicação GUI do Transmissor.
    root.mainloop() # Inicia o ciclo de eventos do Tkinter, mantendo a GUI em execução e responsiva.