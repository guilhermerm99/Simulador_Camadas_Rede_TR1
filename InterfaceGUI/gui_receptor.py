# InterfaceGui/gui_receptor.py
import tkinter as tk
from tkinter import ttk, scrolledtext
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import numpy as np
import threading
import queue
import sys
import time 

# Adiciona o diretório pai ao caminho de busca de módulos para permitir importações locais.
# Isso é necessário para importar o módulo 'receptor' localizado em um nível acima na estrutura de diretórios.
sys.path.append('../')

# Importa o módulo 'receptor' que contém a lógica de backend do simulador de receptor.
# Este módulo gerencia a recepção dos dados da camada física e o processamento de camadas superiores.
from Simulador import receptor 

class ReceptorGUI(ttk.Frame):
    """
    Interface Gráfica do Usuário (GUI) para o Receptor do simulador de camadas de rede.
    Esta classe é responsável por exibir o status da comunicação, as configurações
    da transmissão recebidas, os resultados das etapas de detecção e correção de erros,
    a mensagem final decodificada e os gráficos dos sinais no domínio do tempo.
    """
    def __init__(self, master):
        """
        Inicializa a GUI do Receptor, configurando a janela principal e os componentes.
        
        Args:
            master (tk.Tk): A janela principal do Tkinter à qual este frame será anexado.
        """
        super().__init__(master, padding="10")
        self.master = master
        self.master.title("Simulador de Transmissão - Receptor (Rx)") # Define o título da janela do receptor.
        self.master.geometry("1200x800") # Define o tamanho inicial da janela para uma boa visualização.
        self.pack(fill=tk.BOTH, expand=True) # Faz com que o frame preencha todo o espaço da janela principal.

        # Fila para comunicação thread-safe: permite que a thread do backend (receptor.py)
        # envie atualizações para a thread principal da GUI sem causar travamentos.
        self.update_queue = queue.Queue()

        # Cria e inicializa as variáveis de controle do Tkinter (StringVar) que serão
        # vinculadas aos widgets para atualização dinâmica de texto na interface.
        self._create_variables()
        # Constrói e posiciona todos os elementos visuais (widgets) na GUI.
        self._create_widgets()

        # Inicia uma thread separada para o servidor do receptor. Isso é crucial para
        # que a GUI permaneça responsiva enquanto o receptor aguarda por conexões.
        self.start_listening_thread()
        # Inicia o processamento periódico da fila de atualizações da GUI.
        # Esta função será chamada repetidamente pela thread principal da GUI para manter a GUI atualizada.
        self.process_queue()

    def _create_variables(self):
        """
        Define e inicializa todas as variáveis StringVar do Tkinter que serão usadas
        para exibir dados dinâmicos na interface, como status de conexão, resultados
        de decodificação e configurações de transmissão recebidas.
        """
        self.connection_status_var = tk.StringVar(value="Iniciando...") # Status atual da conexão TCP/IP.
        self.decode_status_var = tk.StringVar(value="Inativo") # Status geral do processo de decodificação do pacote de dados.
        self.detection_method_var = tk.StringVar(value="Detecção:") # Método de detecção de erro configurado.
        self.detection_status_var = tk.StringVar(value="N/A") # Resultado da detecção de erro (e.g., "OK", "INVÁLIDO").
        self.detection_details_var = tk.StringVar(value="") # Informações adicionais sobre a detecção (e.g., valores de CRC).
        self.hamming_status_var = tk.StringVar(value="N/A") # Status da correção de erro via código Hamming.
        
        # Variáveis para exibir as configurações de transmissão que foram recebidas
        # do transmissor como metadados, representando informações da camada de enlace e física.
        self.received_enquadramento_var = tk.StringVar(value="N/A") # Tipo de enquadramento (Camada de Enlace).
        self.received_mod_digital_var = tk.StringVar(value="N/A") # Tipo de modulação digital (Camada Física - Banda Base).
        self.received_mod_portadora_var = tk.StringVar(value="N/A") # Tipo de modulação de portadora (Camada Física - Passa-faixa).
        self.received_detecao_erro_var = tk.StringVar(value="N/A") # Tipo de detecção de erro (Camada de Enlace).
        self.received_correcao_erro_var = tk.StringVar(value="N/A") # Tipo de correção de erro (Camada de Enlace).
        self.received_bit_rate_var = tk.StringVar(value="N/A") # Taxa de bits (Camada Física).
        self.received_freq_var = tk.StringVar(value="N/A") # Frequência da portadora ou fundamental (Camada Física).
        self.received_amplitude_var = tk.StringVar(value="N/A") # Amplitude do sinal (Camada Física).
        self.received_sampling_rate_var = tk.StringVar(value="N/A") # Taxa de amostragem (Camada Física).
        self.received_error_rate_var = tk.StringVar(value="N/A") # Taxa de erros de bit aplicada no canal.

    def _create_widgets(self):
        """
        Constrói a estrutura visual da GUI, organizando os painéis, frames e widgets
        de entrada/saída de informações e os containers para os gráficos.
        """
        # Configura o layout de grid para a janela principal, dividindo-a em duas colunas.
        self.grid_columnconfigure(0, weight=1, minsize=450) # Coluna esquerda para informações de status/config.
        self.grid_columnconfigure(1, weight=2) # Coluna direita para os gráficos, ocupando mais espaço.
        self.grid_rowconfigure(0, weight=1) # A única linha se expande verticalmente.

        # Painel esquerdo: Contém frames para configurações recebidas, status de processamento e mensagem final.
        left_panel = ttk.Frame(self)
        left_panel.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

        # Frame para exibir as configurações da transmissão conforme recebidas do transmissor.
        # Estas configurações são metadados que descrevem o processo de transmissão.
        received_config_frame = ttk.LabelFrame(left_panel, text="Configurações Recebidas", padding="10")
        received_config_frame.pack(fill=tk.X, pady=5) # Preenche a largura do painel esquerdo.
        received_config_frame.grid_columnconfigure(1, weight=1) # Permite que a coluna de valores se expanda.
        
        # Lista de pares (rótulo, variável Tkinter) para criar dinamicamente os rótulos e campos de texto.
        configs = [
            ("Enquadramento:", self.received_enquadramento_var),
            ("Mod. Digital:", self.received_mod_digital_var),
            ("Mod. Portadora:", self.received_mod_portadora_var),
            ("Detecção Erro:", self.received_detecao_erro_var),
            ("Correção Erro:", self.received_correcao_erro_var),
            ("Taxa de Bits:", self.received_bit_rate_var),
            ("Frequência:", self.received_freq_var),
            ("Amplitude:", self.received_amplitude_var),
            ("Taxa Amostragem:", self.received_sampling_rate_var),
            ("Taxa de Erros Aplicada:", self.received_error_rate_var)
        ]
        # Itera sobre a lista para criar cada linha de configuração (rótulo + valor).
        for i, (label_text, var) in enumerate(configs):
            ttk.Label(received_config_frame, text=label_text).grid(row=i, column=0, sticky="w", padx=2, pady=1)
            ttk.Label(received_config_frame, textvariable=var, foreground="#333").grid(row=i, column=1, sticky="w", padx=2, pady=1)

        # Frame para exibir o status atual de cada etapa do processamento de recepção.
        status_process_frame = ttk.LabelFrame(left_panel, text="Status do Processamento", padding="10")
        status_process_frame.pack(fill=tk.X, pady=10)
        status_process_frame.grid_columnconfigure(1, weight=1) # Permite que a coluna de status se expanda.
        
        # Linhas de status para a conexão, decodificação geral e status da correção de Hamming.
        self.connection_status_label = self.create_status_row(status_process_frame, 0, "Status Conexão:", self.connection_status_var)
        self.decode_status_label = self.create_status_row(status_process_frame, 1, "Status Decodificação:", self.decode_status_var)
        self.hamming_status_label = self.create_status_row(status_process_frame, 2, "Status Hamming:", self.hamming_status_var)

        # Rótulos específicos para o método de detecção de erro e seus detalhes.
        # A detecção de erro (Camada de Enlace) pode usar paridade ou CRC.
        self.detection_method_label = ttk.Label(status_process_frame, textvariable=self.detection_method_var)
        self.detection_method_label.grid(row=3, column=0, sticky="w", padx=2, pady=1)
        self.detection_status_label = ttk.Label(status_process_frame, textvariable=self.detection_status_var)
        self.detection_status_label.grid(row=3, column=1, sticky="w", padx=2, pady=1)
        self.detection_details_label = ttk.Label(status_process_frame, textvariable=self.detection_details_var, font=('TkFixedFont', 8), wraplength=350)
        self.detection_details_label.grid(row=4, column=0, columnspan=2, sticky="w", padx=2, pady=1)

        # Frame para exibir a mensagem final decodificada, com scrollbar.
        received_msg_frame = ttk.LabelFrame(left_panel, text="Mensagem Final Recebida", padding="10")
        received_msg_frame.pack(fill=tk.BOTH, expand=True, pady=10) # Preenche o espaço restante verticalmente.
        self.received_message_text = scrolledtext.ScrolledText(received_msg_frame, wrap=tk.WORD, height=4, state="disabled", font=("Helvetica", 12))
        self.received_message_text.pack(fill=tk.BOTH, expand=True)

        # Painel direito: Contém o notebook para os gráficos.
        plot_container_frame = ttk.LabelFrame(self, text="Gráficos do Sinal Recebido", padding="10")
        plot_container_frame.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")
        
        # Notebook (abas) para organizar os diferentes gráficos de sinal.
        self.plot_notebook = ttk.Notebook(plot_container_frame)
        self.plot_notebook.pack(fill=tk.BOTH, expand=True)

        # Criação das abas de gráficos: Sinal Recebido (pré-demodulação) e Bits Recebidos (pós-demodulação).
        # Cada aba inclui um gráfico Matplotlib com sua própria barra de ferramentas de navegação.
        self.ax_pre, self.canvas_pre = self.create_plot_tab("Sinal RX") # Gráfico do sinal recebido no canal (Camada Física).
        self.ax_post, self.canvas_post = self.create_plot_tab("Bits RX") # Gráfico do sinal digital após demodulação (Camada Física - Banda Base).
        # NOVO: Aba para o gráfico da constelação recebida (com ruído).
        self.ax_const_rx, self.canvas_const_rx = self.create_plot_tab("Constelação 8-QAM (RX)", figsize=(8, 6))

    def create_plot_tab(self, name, figsize=(6, 3)):
        """
        Cria uma nova aba dentro do notebook de gráficos, configurando um gráfico Matplotlib
        com um canvas Tkinter e uma barra de ferramentas de navegação (zoom, pan).
        
        Args:
            name (str): O nome que será exibido na aba e como título inicial do gráfico.
            figsize (tuple): O tamanho da figura Matplotlib (largura, altura em polegadas).
            
        Returns:
            tuple: Uma tupla contendo o objeto 'Axes' do Matplotlib e o 'FigureCanvasTkAgg' do Tkinter.
        """
        tab = ttk.Frame(self.plot_notebook) # Cria um novo frame que servirá como o conteúdo da aba.
        self.plot_notebook.add(tab, text=name) # Adiciona este frame como uma nova aba ao notebook.
        fig, ax = plt.subplots(figsize=figsize) # Cria uma nova figura e um conjunto de eixos para o gráfico.
        canvas = FigureCanvasTkAgg(fig, master=tab) # Integra a figura Matplotlib ao ambiente Tkinter.
        toolbar = NavigationToolbar2Tk(canvas, tab) # Adiciona a barra de ferramentas padrão do Matplotlib (zoom, pan, salvar).
        toolbar.update() # Garante que a barra de ferramentas seja renderizada corretamente.
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True) # Empacota o widget do canvas para preencher a aba.
        self.clear_plot_ax(ax, canvas, title=name) # Limpa o gráfico e define o título inicial.
        return ax, canvas

    def clear_plot_ax(self, ax, canvas, title):
        """
        Limpa o conteúdo de um conjunto de eixos Matplotlib e redesenha o canvas associado.
        Utilizado para preparar o gráfico para uma nova plotagem.
        
        Args:
            ax (matplotlib.axes.Axes): O objeto de eixos do Matplotlib a ser limpo.
            canvas (FigureCanvasTkAgg): O canvas Tkinter associado ao eixo.
            title (str): O título que será definido para o eixo após a limpeza.
        """
        ax.clear() # Remove todas as linhas, pontos e textos do eixo.
        ax.set_title(title, fontsize=10) # Define o título do eixo.
        ax.grid(True, linestyle='--', linewidth=0.5) # Adiciona uma grade ao gráfico para facilitar a leitura.
        canvas.draw() # Força o redesenho do canvas para que as mudanças sejam visíveis.

    def plot_pre_demod(self, data):
        """
        Atualiza o gráfico que exibe o sinal recebido no canal, antes de qualquer demodulação.
        Este é tipicamente um sinal analógico ou com ruído, representando a Camada Física.
        
        Args:
            data (dict): Dicionário contendo 't' (eixo de tempo), 'signal_real' (dados do sinal),
                         e 'config' (configurações da transmissão para o título).
        """
        ax, canvas = self.ax_pre, self.canvas_pre
        # Limpa o gráfico e define o título, incluindo o tipo de modulação de portadora.
        self.clear_plot_ax(ax, canvas, f"Sinal Recebido (Pré-Demod) - {data['config']['mod_portadora_type']}") 
        ax.plot(data['t'], data['signal_real'], color='blue', linewidth=1) # Plota o sinal como uma linha contínua.
        ax.set_xlabel("Tempo (s)") # Rótulo do eixo X.
        ax.set_ylabel("Amplitude") # Rótulo do eixo Y.
        
        # Ajusta o limite do eixo X para focar em uma janela de tempo razoável (e.g., 2.5 segundos)
        # ou no comprimento total do sinal se for menor, para melhor visualização.
        window_duration = 2.5 # segundos
        ax.set_xlim(0, min(window_duration, data['t'][-1] if len(data['t']) > 0 else 1))
        
        # Ajusta o limite do eixo Y com uma margem para garantir que todo o sinal seja visível.
        if len(data['signal_real']) > 0:
            margin = (max(data['signal_real']) - min(data['signal_real'])) * 0.1
            ax.set_ylim(min(data['signal_real']) - margin, max(data['signal_real']) + margin)
        canvas.draw() # Redesenha o canvas para atualizar o gráfico na GUI.

    def plot_post_demod(self, data):
        """
        Atualiza o gráfico que exibe o sinal digital reconstruído após a demodulação.
        Este gráfico mostra a forma de onda digital (e.g., NRZ-Polar, Manchester),
        representando a Camada Física na banda base.
        
        Args:
            data (dict): Dicionário contendo 't' (eixo de tempo), 'signal' (dados do sinal digital),
                         e 'config' (configurações da transmissão para o título).
        """
        ax, canvas = self.ax_post, self.canvas_post
        config = data['config']
        # Limpa o gráfico e define o título, incluindo o tipo de modulação digital.
        self.clear_plot_ax(ax, canvas, f"Bits Recuperados ({config['mod_digital_type']})") 
        ax.step(data['t'], data['signal'], where='post', color='dodgerblue', linewidth=1.2) # Plota o sinal como degraus para representar bits.
        ax.set_xlabel("Tempo (s)") # Rótulo do eixo X.
        ax.set_ylabel("Nível Lógico") # Rótulo do eixo Y.
        
        # Ajusta o limite do eixo X para focar em uma janela de tempo menor (e.g., 0.05 segundos)
        # para visualizar os bits individuais, ou o total do sinal se for menor.
        window_duration = 0.05 # segundos
        ax.set_xlim(0, min(window_duration, data['t'][-1] if len(data['t']) > 0 else 1))
        
        # Ajusta o limite do eixo Y com uma margem para sinais digitais.
        if len(data['signal']) > 0:
            min_val = np.min(data['signal'])
            max_val = np.max(data['signal'])
            y_margin = (max_val - min_val) * 0.1 if (max_val - min_val) > 0 else 0.2
            ax.set_ylim(min_val - y_margin, max_val + y_margin)
        canvas.draw() # Redesenha o canvas para atualizar o gráfico na GUI.

    def plot_constellation_rx(self, plot_data):
        """
        Atualiza o gráfico da constelação recebida no receptor, incluindo o ruído.
        Este gráfico mostra os pontos no plano I/Q tal como foram recebidos após a demodulação,
        permitindo visualizar o impacto do ruído nos símbolos.
        
        Args:
            plot_data (dict): Dicionário contendo 'points' (lista de pontos complexos da constelação ruidosa).
        """
        ax, canvas = self.ax_const_rx, self.canvas_const_rx
        points = plot_data['points']
        self.clear_plot_ax(ax, canvas, "Constelação 8-QAM Recebida (com Ruído)") # Limpa e define o título.
        real = [p.real for p in points] # Extrai as componentes em fase (I).
        imag = [p.imag for p in points] # Extrai as componentes em quadratura (Q).
        ax.scatter(real, imag, color='purple', s=40, alpha=0.8, edgecolors='black', linewidths=0.5) # Plota os pontos.
        
        # Desenha as linhas dos eixos I e Q.
        ax.axhline(0, color='gray', lw=0.5)
        ax.axvline(0, color='gray', lw=0.5)
        ax.set_xlabel("Em Fase (I)")
        ax.set_ylabel("Quadratura (Q)")
        
        # Ajusta os limites dos eixos para garantir que todos os pontos e o centro (0,0) sejam visíveis.
        # Adiciona uma margem extra para melhor visualização, especialmente se houver ruído.
        all_coords = real + imag
        if all_coords:
            max_abs_val = max(abs(val) for val in all_coords)
            limit = max_abs_val * 1.5 # Margem maior para visualizar a dispersão do ruído.
            ax.set_xlim(-limit, limit)
            ax.set_ylim(-limit, limit)
        else: # Caso não haja pontos (ex: se a modulação não for 8-QAM).
            ax.set_xlim(-1.5, 1.5)
            ax.set_ylim(-1.5, 1.5)

        ax.set_aspect('equal', 'box') # Garante que os eixos tenham a mesma escala para uma representação fiel.
        canvas.draw() # Redesenha o canvas.


    def process_queue(self):
        """
        Processa as mensagens na fila de atualização da GUI.
        Esta função é o coração da comunicação entre a thread de backend do receptor
        e a thread principal da GUI, garantindo que as atualizações sejam seguras.
        É chamada periodicamente através de `master.after()`.
        """
        try:
            while not self.update_queue.empty(): # Processa todas as mensagens que estão na fila.
                msg = self.update_queue.get_nowait() # Obtém uma mensagem da fila sem bloquear.
                msg_type = msg.get('type') # Extrai o tipo da mensagem para direcionar a atualização.

                # Direciona a mensagem para a função de atualização apropriada na GUI.
                if msg_type == 'new_connection':
                    self.clear_all_for_new_connection(msg['address']) # Limpa a GUI e prepara para nova conexão.
                elif msg_type == 'connection_status':
                    self.update_status_var(self.connection_status_label, self.connection_status_var, msg) # Atualiza o status da conexão.
                elif msg_type == 'decode_status':
                    self.update_status_var(self.decode_status_label, self.decode_status_var, msg) # Atualiza o status da decodificação.
                elif msg_type == 'hamming_status':
                    self.update_status_var(self.hamming_status_label, self.hamming_status_var, msg) # Atualiza o status da correção Hamming (Camada de Enlace).
                elif msg_type == 'received_configs':
                    self.update_received_configs(msg['data']) # Atualiza as configurações de transmissão recebidas.
                elif msg_type == 'detection_result':
                    self.update_detection_display(msg['data']) # Atualiza o display de detecção de erros (Camada de Enlace).
                elif msg_type == 'final_message':
                    self.update_received_message(msg['message']) # Atualiza a área de texto da mensagem final.
                elif msg_type == 'plot':
                    self.dispatch_plot(msg['tab'], msg['data']) # Despacha os dados para a função de plotagem de gráfico.
        finally:
            # Agenda a próxima chamada desta função após 100 milissegundos.
            # Isso cria um loop de eventos que mantém a GUI responsiva e processa as atualizações da fila.
            self.master.after(100, self.process_queue)

    def update_detection_display(self, data):
        """
        Atualiza os rótulos na GUI que exibem o resultado da detecção de erros (Camada de Enlace).
        
        Args:
            data (dict): Dicionário contendo 'method' (método de detecção), 'status' (OK/INVÁLIDO),
                         e detalhes como 'calc' e 'recv' para CRC-32.
        """
        method = data.get('method')
        status = data.get('status')
        # Define a cor do texto do status com base no resultado da detecção para feedback visual.
        color = "green" if "OK" in status else "red" if "INVÁLIDO" in status else "black"
        self.detection_details_var.set("") # Limpa quaisquer detalhes de detecção anteriores.

        if method == "Nenhuma":
            self.detection_method_var.set("Detecção de Erro:")
            self.detection_status_var.set("N/A (desativada)")
            self.detection_status_label.config(foreground="black")
        elif method == "Paridade Par": # Método de detecção de erro por paridade (Camada de Enlace).
            self.detection_method_var.set("Status Paridade:")
            self.detection_status_var.set(status)
            self.detection_status_label.config(foreground=color)
        elif method == "CRC-32": # Método de detecção de erro CRC-32 (Camada de Enlace).
            self.detection_method_var.set("Status CRC-32:")
            self.detection_status_var.set(status)
            self.detection_status_label.config(foreground=color)
            calc = data.get('calc')
            recv = data.get('recv')
            # Exibe os valores binários do CRC calculado localmente e do CRC recebido para comparação.
            details_text = f"Calculado: 0b{calc:032b}\nRecebido:  0b{recv:032b}"
            self.detection_details_var.set(details_text)

    def clear_all_for_new_connection(self, address):
        """
        Reinicializa todos os campos de exibição e limpa os gráficos na GUI
        quando uma nova conexão de transmissão é estabelecida.
        Prepara a interface para uma nova rodada de simulação.
        
        Args:
            address (str): O endereço IP do cliente que se conectou.
        """
        self.connection_status_var.set(f"Conexão de {address}") # Exibe o endereço do cliente conectado.
        self.connection_status_label.config(foreground='green') # Define a cor do status para indicar conexão ativa.
        
        # Reseta todas as variáveis de status e configuração para seus valores iniciais ou placeholders.
        for var in [self.decode_status_var, self.detection_status_var, self.hamming_status_var,
                    self.received_enquadramento_var, self.received_mod_digital_var,
                    self.received_mod_portadora_var, self.received_detecao_erro_var,
                    self.received_correcao_erro_var, self.received_bit_rate_var,
                    self.received_freq_var, self.received_amplitude_var,
                    self.received_sampling_rate_var, self.received_error_rate_var]:
            var.set("...") # Define um valor temporário de "..." ou "N/A" para indicar que os dados estão sendo aguardados.
        self.detection_method_var.set("Detecção:")
        self.detection_details_var.set("")

        # Limpa a área de texto que exibe a mensagem final decodificada.
        self.received_message_text.config(state="normal")
        self.received_message_text.delete(1.0, tk.END)
        self.received_message_text.config(state="disabled")
        
        # Limpa os eixos de plotagem para os gráficos de sinal recebido (Camada Física) e bits demodulados (Camada Física).
        for ax, canvas, title in [
            (self.ax_pre, self.canvas_pre, "Sinal RX"),
            (self.ax_post, self.canvas_post, "Bits RX"),
            (self.ax_const_rx, self.canvas_const_rx, "Constelação 8-QAM (RX)") # Adiciona a nova aba de constelação para limpeza.
        ]:
            self.clear_plot_ax(ax, canvas, title)

    def create_status_row(self, parent, row, text, var):
        """
        Cria uma linha de exibição de status genérica dentro de um frame,
        consistindo de um rótulo fixo e um rótulo dinâmico vinculado a uma StringVar.
        
        Args:
            parent (ttk.Frame): O frame pai onde a linha será adicionada.
            row (int): O número da linha no grid do frame pai.
            text (str): O texto do rótulo fixo (e.g., "Status Conexão:").
            var (tk.StringVar): A variável Tkinter que conterá o texto dinâmico.
            
        Returns:
            ttk.Label: O widget Label dinâmico criado.
        """
        ttk.Label(parent, text=text).grid(row=row, column=0, sticky="w", padx=2, pady=1)
        label = ttk.Label(parent, textvariable=var)
        label.grid(row=row, column=1, sticky="w", padx=2, pady=1)
        return label

    def start_listening_thread(self):
        """
        Inicia o servidor do receptor (lógica de backend) em uma thread separada.
        Isso permite que a GUI permaneça responsiva enquanto o servidor aguarda
        e processa as transmissões recebidas, sem bloquear a interface.
        """
        thread = threading.Thread(target=receptor.run_receiver, args=(self.gui_update_callback,))
        thread.daemon = True # Define a thread como daemon para garantir que ela seja encerrada
                             # automaticamente quando o programa principal (GUI) for fechado.
        thread.start()

    def gui_update_callback(self, msg):
        """
        Função de callback chamada pela thread do receptor para enviar mensagens
        de atualização para a fila da GUI. Esta é a ponte thread-safe para
        atualizar elementos da GUI a partir de uma thread secundária.
        
        Args:
            msg (dict): Dicionário contendo o tipo e os dados da atualização.
        """
        self.update_queue.put(msg) # Adiciona a mensagem à fila para processamento posterior pela thread da GUI.

    def update_status_var(self, label, var, msg):
        """
        Atualiza o texto e a cor de um rótulo de status na GUI.
        
        Args:
            label (ttk.Label): O widget Label a ser atualizado.
            var (tk.StringVar): A StringVar associada ao Label.
            msg (dict): Dicionário contendo 'message' (o texto a ser exibido) e 'color' (a cor do texto).
        """
        var.set(msg['message']) # Define o texto da variável.
        label.config(foreground=msg['color']) # Define a cor do texto do rótulo.

    def dispatch_plot(self, tab, data):
        """
        Direciona os dados de plotagem para a função de plotagem de gráfico apropriada,
        com base na aba/tipo de gráfico especificado.
        
        Args:
            tab (str): O nome da aba/tipo de gráfico a ser atualizado ('pre_demod', 'post_demod', 'constellation_rx').
            data (dict): Os dados de plotagem a serem passados para a função de plotagem.
        """
        if tab == 'pre_demod': self.plot_pre_demod(data) # Atualiza o gráfico do sinal recebido (pré-demodulação - Camada Física).
        elif tab == 'post_demod': self.plot_post_demod(data) # Atualiza o gráfico dos bits recuperados (pós-demodulação - Camada Física).
        elif tab == 'constellation_rx': self.plot_constellation_rx(data) # NOVO: Atualiza o gráfico da constelação recebida (com ruído).

    def update_received_configs(self, data):
        """
        Atualiza as variáveis da GUI com as configurações de transmissão recebidas
        do transmissor, que atuam como metadados do processo de simulação.
        
        Args:
            data (dict): Dicionário contendo as configurações de transmissão.
        """
        self.received_enquadramento_var.set(data.get("enquadramento_type"))
        self.received_mod_digital_var.set(data.get("mod_digital_type"))
        self.received_mod_portadora_var.set(data.get("mod_portadora_type"))
        self.received_detecao_erro_var.set(data.get("detecao_erro_type"))
        self.received_correcao_erro_var.set(data.get("correcao_erro_type"))
        self.received_bit_rate_var.set(f"{data.get('bit_rate')} bps")
        self.received_freq_var.set(f"{data.get('freq_base')} Hz")
        self.received_amplitude_var.set(f"{data.get('amplitude')} V")
        self.received_sampling_rate_var.set(f"{data.get('sampling_rate')} sps")
        self.received_error_rate_var.set(f"{data.get('taxa_erros'):.3f}")

    def update_received_message(self, message):
        """
        Atualiza a área de texto da GUI com a mensagem final decodificada,
        após todo o processamento de camadas (física e enlace).
        
        Args:
            message (str): A mensagem de texto decodificada.
        """
        self.received_message_text.config(state="normal") # Habilita temporariamente a área de texto para edição.
        self.received_message_text.delete(1.0, tk.END) # Limpa qualquer conteúdo existente na área de texto.
        self.received_message_text.insert(tk.END, message) # Insere a nova mensagem decodificada.
        self.received_message_text.config(state="disabled") # Desabilita a área de texto novamente para evitar edição pelo usuário.

if __name__ == '__main__':
    root = tk.Tk() # Cria a janela principal do Tkinter.
    app = ReceptorGUI(root) # Instancia a aplicação GUI do Receptor.
    root.mainloop() # Inicia o loop de eventos do Tkinter, mantendo a GUI em execução e responsiva.