# InterfaceGUI/interface_tkinter.py

import tkinter as tk
from tkinter import ttk, messagebox
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk

# Módulos para gerenciar caminhos de importação
import sys
import os

# Adiciona os diretórios necessários ao PATH para que o Python encontre os módulos.
# O '..' sobe um nível (para a pasta raiz do projeto) e o '..', 'Simulador' adiciona o diretório do Simulador.
# Isso é crucial para que 'from Simulador.main import SimuladorRedes' funcione.
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'Simulador')))

# Tenta importar a classe SimuladorRedes do módulo main.py.
# Um bloco try-except é usado para capturar erros de importação e fornecer feedback ao usuário.
try:
    from Simulador.main import SimuladorRedes
except ImportError as e:
    # Se a importação falhar, exibe uma mensagem de erro e sai do aplicativo.
    messagebox.showerror("Erro de Importação", f"Não foi possível importar SimuladorRedes."
                                               f" Verifique a estrutura de pastas do projeto (deve ser executado da raiz ou InterfaceGUI)."
                                               f" Erro: {e}")
    sys.exit(1)


class NetworkSimulatorGUI:
    """
    Interface Gráfica do Usuário (GUI) para o Simulador de Redes.
    Permite ao usuário configurar os parâmetros da simulação (enquadramento, modulações, detecção/correção de erros, taxa de erros)
    e visualizar os resultados da transmissão de dados, incluindo gráficos dos sinais.
    """
    def __init__(self, master: tk.Tk):
        """
        Inicializa a GUI do simulador.

        Args:
            master (tk.Tk): A janela principal do Tkinter (root).
        """
        self.master = master
        master.title("Simulador de Redes - TR1") # Título da janela
        master.geometry("1200x800") # Define o tamanho inicial da janela

        # Instancia o simulador principal que contém a lógica das camadas.
        self.simulador = SimuladorRedes() 

        # --- Variáveis de Controle do Tkinter ---
        # StringVar para campos de texto editáveis ou exibição.
        self.text_input_var = tk.StringVar(value="Olá mundo!") # Texto a ser transmitido
        self.tx_output_bits_var = tk.StringVar() # Saída de bits após TX (enlace)
        self.rx_output_bits_var = tk.StringVar() # Saída de bits após RX (enlace)
        self.rx_output_text_var = tk.StringVar() # Texto final decodificado no RX (aplicação)

        # StringVar para seleção de opções via OptionMenu. Valores padrão são definidos.
        self.enquadramento_type_var = tk.StringVar(value='Contagem de caracteres')
        self.mod_digital_type_var = tk.StringVar(value='NRZ-Polar')
        self.mod_portadora_type_var = tk.StringVar(value='ASK')
        self.detecao_erro_type_var = tk.StringVar(value='Nenhuma')
        self.correcao_erro_type_var = tk.StringVar(value='Nenhuma') 
        
        # DoubleVar para o slider da taxa de erros (permite valores decimais).
        self.taxa_erros_var = tk.DoubleVar(value=0.0) 

        # --- Configuração do Layout da GUI (usando ttk para estilo moderno) ---
        main_frame = ttk.Frame(master, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True) # Preenche toda a janela e expande com ela

        # Frame para as configurações do simulador (coluna da esquerda).
        config_frame = ttk.LabelFrame(main_frame, text="Configurações da Simulação", padding="10")
        config_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        main_frame.grid_columnconfigure(0, weight=1) # Permite que a coluna de configurações se expanda
        main_frame.grid_rowconfigure(0, weight=1)    # Permite que a linha principal se expanda

        # Widgets de entrada e seleção de protocolo
        ttk.Label(config_frame, text="Texto de Entrada para Transmissão:").pack(pady=5)
        ttk.Entry(config_frame, textvariable=self.text_input_var, width=40).pack(pady=5)

        ttk.Label(config_frame, text="1. Tipo de Enquadramento:").pack(pady=5)
        # OptionMenu para selecionar o protocolo de enquadramento. As opções são obtidas do simulador.
        ttk.OptionMenu(config_frame, self.enquadramento_type_var,
                       self.enquadramento_type_var.get(),
                       *list(self.simulador.get_enquadramento_options().keys())).pack(pady=5)

        ttk.Label(config_frame, text="2. Modulação Digital (Banda-Base):").pack(pady=5)
        ttk.OptionMenu(config_frame, self.mod_digital_type_var,
                       self.mod_digital_type_var.get(),
                       *list(self.simulador.get_mod_digital_options().keys())).pack(pady=5)

        ttk.Label(config_frame, text="3. Modulação por Portadora:").pack(pady=5)
        ttk.OptionMenu(config_frame, self.mod_portadora_type_var,
                       self.mod_portadora_type_var.get(),
                       *list(self.simulador.get_mod_portadora_options().keys())).pack(pady=5)

        ttk.Label(config_frame, text="4. Detecção de Erros:").pack(pady=5)
        ttk.OptionMenu(config_frame, self.detecao_erro_type_var,
                       self.detecao_erro_type_var.get(),
                       *list(self.simulador.get_deteccao_erro_options().keys())).pack(pady=5)

        ttk.Label(config_frame, text="5. Correção de Erros:").pack(pady=5)
        ttk.OptionMenu(config_frame, self.correcao_erro_type_var,
                       self.correcao_erro_type_var.get(),
                       *list(self.simulador.get_correcao_erro_options().keys())).pack(pady=5)

        # Slider para ajustar a taxa de erros no canal.
        ttk.Label(config_frame, text="6. Taxa de Erros no Canal (0.0 a 0.1):").pack(pady=5)
        self.error_rate_scale = ttk.Scale(config_frame, from_=0.0, to_=0.1, orient=tk.HORIZONTAL,
                                          variable=self.taxa_erros_var,
                                          command=self._update_taxa_erros_label) # Chama função ao mover slider
        self.error_rate_scale.pack(pady=5, fill=tk.X)
        self.taxa_erros_label = ttk.Label(config_frame, text=f"Atual: {self.taxa_erros_var.get():.3f}")
        self.taxa_erros_label.pack()

        # Botão para iniciar a simulação.
        ttk.Button(config_frame, text="Iniciar Simulação", command=self.run_simulation).pack(pady=20)

        # Frame para os resultados e gráficos (coluna da direita).
        results_frame = ttk.Frame(main_frame, padding="10")
        results_frame.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")
        main_frame.grid_columnconfigure(1, weight=3) # Coluna de resultados/gráficos ocupa mais espaço

        # Notebook para organizar as abas de "Saídas de Texto" e "Gráficos de Sinais".
        self.notebook = ttk.Notebook(results_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        # --- Aba de Saídas de Texto ---
        text_output_tab = ttk.Frame(self.notebook)
        self.notebook.add(text_output_tab, text="Saídas de Texto")

        ttk.Label(text_output_tab, text="Saída de Bits Transmitidos (Camada de Enlace TX):").pack(pady=5)
        # Widget Text para exibir bits transmitidos. Configurado como somente leitura.
        self.tx_output_text = tk.Text(text_output_tab, wrap=tk.WORD, height=6, width=80)
        self.tx_output_text.pack(fill=tk.X, expand=True)
        self.tx_output_text.config(state=tk.DISABLED) # Desabilitado para edição pelo usuário

        ttk.Label(text_output_tab, text="Saída de Bits Recebidos (Camada de Enlace RX):").pack(pady=5)
        # Widget Text para exibir bits recebidos após processamento da camada de enlace RX.
        self.rx_output_bits_text = tk.Text(text_output_tab, wrap=tk.WORD, height=6, width=80)
        self.rx_output_bits_text.pack(fill=tk.X, expand=True)
        self.rx_output_bits_text.config(state=tk.DISABLED)

        ttk.Label(text_output_tab, text="Texto Final Recebido (Camada de Aplicação RX):").pack(pady=5)
        # Widget Text para exibir o texto final decodificado no receptor.
        self.rx_output_final_text = tk.Text(text_output_tab, wrap=tk.WORD, height=6, width=80)
        self.rx_output_final_text.pack(fill=tk.X, expand=True)
        self.rx_output_final_text.config(state=tk.DISABLED)

        # --- Aba de Gráficos de Sinais ---
        self.plot_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.plot_tab, text="Gráficos de Sinais")

        # Configura a figura e eixos do Matplotlib para plotagem do sinal.
        self.fig, self.ax = plt.subplots(figsize=(10, 6)) # Tamanho da figura para o gráfico
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.plot_tab) # Integra a figura ao Tkinter
        self.canvas_widget = self.canvas.get_tk_widget()
        self.canvas_widget.pack(fill=tk.BOTH, expand=True)

        # Adiciona a barra de ferramentas de navegação do Matplotlib (zoom, pan, save).
        self.toolbar = NavigationToolbar2Tk(self.canvas, self.plot_tab)
        self.toolbar.update()
        # O canvas_widget já está empacotado, esta linha era redundante e foi movida para acima.
        # self.canvas_widget.pack(fill=tk.BOTH, expand=True)

        self.clear_plot() # Limpa e configura o gráfico inicialmente.

    def _update_taxa_erros_label(self, val: str):
        """
        Atualiza o texto do label que mostra a taxa de erros atual do slider.

        Args:
            val (str): O valor atual do slider como string.
        """
        self.taxa_erros_label.config(text=f"Atual: {float(val):.3f}")

    def clear_plot(self):
        """
        Limpa o gráfico atual, redefine o título e rótulos, e desenha um gráfico vazio.
        Chamado na inicialização e antes de cada nova plotagem.
        """
        self.ax.clear() # Limpa o conteúdo dos eixos
        self.ax.set_title("Gráfico de Sinais Modulados (Transmissor)")
        self.ax.set_xlabel("Amostras do Sinal")
        self.ax.set_ylabel("Amplitude do Sinal")
        self.ax.grid(True) # Adiciona uma grade ao gráfico
        self.canvas.draw() # Redesenha o canvas para mostrar as alterações

    def update_text_output(self, tx_bits: str, rx_bits: str, rx_text: str):
        """
        Atualiza os Text widgets com as saídas da simulação.
        Temporariamente habilita os widgets para inserir o texto, e depois os desabilita.

        Args:
            tx_bits (str): A string de bits transmitida.
            rx_bits (str): A string de bits recebida (após camada de enlace RX).
            rx_text (str): O texto final decodificado no receptor.
        """
        # Habilita o widget, limpa o conteúdo e insere o novo texto para TX Bits
        self.tx_output_text.config(state=tk.NORMAL)
        self.tx_output_text.delete(1.0, tk.END)
        self.tx_output_text.insert(tk.END, tx_bits)
        self.tx_output_text.config(state=tk.DISABLED) # Desabilita novamente

        # Habilita, limpa e insere para RX Bits
        self.rx_output_bits_text.config(state=tk.NORMAL)
        self.rx_output_bits_text.delete(1.0, tk.END)
        self.rx_output_bits_text.insert(tk.END, rx_bits)
        self.rx_output_bits_text.config(state=tk.DISABLED)

        # Habilita, limpa e insere para Texto Final RX
        self.rx_output_final_text.config(state=tk.NORMAL)
        self.rx_output_final_text.delete(1.0, tk.END)
        self.rx_output_final_text.insert(tk.END, rx_text)
        self.rx_output_final_text.config(state=tk.DISABLED)

    def run_simulation(self):
        """
        Executa a simulação de rede com base nas configurações selecionadas pelo usuário.
        Coleta os parâmetros, chama o método de simulação do SimuladorRedes,
        e atualiza as saídas de texto e o gráfico de sinal.
        """
        # Coleta o texto de entrada do usuário.
        input_text = self.text_input_var.get()
        
        # Cria um dicionário com todas as configurações selecionadas na GUI.
        config = {
            'tipo_enquadramento': self.enquadramento_type_var.get(),
            'tipo_modulacao_digital': self.mod_digital_type_var.get(),
            'tipo_modulacao_portadora': self.mod_portadora_type_var.get(),
            'tipo_detecao_erro': self.detecao_erro_type_var.get(),
            'tipo_correcao_erro': self.correcao_erro_type_var.get(),
            'taxa_erros': self.taxa_erros_var.get()
        }

        try:
            # Chama o método principal do simulador, que executa toda a cadeia de transmissão e recepção.
            # Ele retorna os bits processados no TX, os bits recebidos no RX, o texto final RX e os dados do sinal para plotagem.
            tx_bits_output, rx_bits_output, rx_text_output, signal_plot_data = \
                self.simulador.simular_transmissao_receptor(input_text, config)

            # Atualiza os Text widgets com as saídas da simulação.
            self.update_text_output(tx_bits_output, rx_bits_output, rx_text_output)

            # Atualiza o gráfico do sinal.
            self.ax.clear() # Limpa os eixos antes de plotar o novo sinal
            self.ax.plot(signal_plot_data) # Plota o sinal modulado
            self.ax.set_title(f"Sinal Modulado Transmitido ({config['tipo_modulacao_digital']} + {config['tipo_modulacao_portadora']})")
            self.ax.set_xlabel("Amostras do Sinal")
            self.ax.set_ylabel("Amplitude do Sinal")
            self.ax.grid(True)
            self.canvas.draw() # Desenha o gráfico atualizado no canvas do Tkinter
            self.notebook.select(self.plot_tab) # Muda automaticamente para a aba do gráfico

            # Exibe uma mensagem de sucesso ao usuário.
            messagebox.showinfo("Simulação Concluída", "A simulação foi executada com sucesso!")

        except ValueError as e:
            # Captura erros específicos de validação de dados ou lógica de protocolo.
            messagebox.showerror("Erro de Simulação", f"Erro nas configurações ou dados: {e}")
        except Exception as e:
            # Captura qualquer outro erro inesperado e exibe uma mensagem genérica.
            messagebox.showerror("Erro Inesperado", f"Ocorreu um erro inesperado durante a simulação: {e}")

# Ponto de entrada principal do aplicativo GUI.
if __name__ == "__main__":
    root = tk.Tk() # Cria a janela principal do Tkinter
    app = NetworkSimulatorGUI(root) # Instancia a GUI
    root.mainloop() # Inicia o loop de eventos do Tkinter, mantendo a janela aberta