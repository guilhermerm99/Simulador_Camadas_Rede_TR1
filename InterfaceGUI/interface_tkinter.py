# InterfaceGUI/interface_tkinter.py

import tkinter as tk
from tkinter import ttk, messagebox
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk

# Importar o simulador principal
import sys
import os
# Adiciona o diretório pai (Simulador/) ao PATH para encontrar os módulos
# Certifique-se de que o diretório principal do projeto (Simulador_Camadas_Rede_TR1) está no PATH
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'Simulador')))

# Tenta importar SimuladorRedes do módulo main
try:
    from Simulador.main import SimuladorRedes
except ImportError as e:
    messagebox.showerror("Erro de Importação", f"Não foi possível importar SimuladorRedes. Verifique a estrutura de pastas e o PATH. Erro: {e}")
    sys.exit(1)


class NetworkSimulatorGUI:
    def __init__(self, master):
        self.master = master
        master.title("Simulador de Redes - TR1")
        master.geometry("1200x800") # Aumenta o tamanho da janela

        self.simulador = SimuladorRedes() # Instancia o simulador

        # --- Variáveis de Controle ---
        self.text_input_var = tk.StringVar(value="Olá mundo!")
        self.tx_output_bits_var = tk.StringVar()
        self.rx_output_bits_var = tk.StringVar()
        self.rx_output_text_var = tk.StringVar()

        self.enquadramento_type_var = tk.StringVar(value='Contagem de caracteres')
        self.mod_digital_type_var = tk.StringVar(value='NRZ-Polar')
        self.mod_portadora_type_var = tk.StringVar(value='ASK')
        self.detecao_erro_type_var = tk.StringVar(value='CRC-32')
        self.correcao_erro_type_var = tk.StringVar(value='Nenhuma') # PADRÃO AGORA É NENHUMA
        self.taxa_erros_var = tk.DoubleVar(value=0.0) # Taxa de erro inicial

        # --- Layout da GUI ---
        main_frame = ttk.Frame(master, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Frame de Configurações (Esquerda)
        config_frame = ttk.LabelFrame(main_frame, text="Configurações", padding="10")
        config_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        main_frame.grid_columnconfigure(0, weight=1)
        main_frame.grid_rowconfigure(0, weight=1)

        ttk.Label(config_frame, text="Texto de Entrada:").pack(pady=5)
        ttk.Entry(config_frame, textvariable=self.text_input_var, width=40).pack(pady=5)

        ttk.Label(config_frame, text="Tipo de Enquadramento:").pack(pady=5)
        ttk.OptionMenu(config_frame, self.enquadramento_type_var,
                       self.enquadramento_type_var.get(),
                       *list(self.simulador.get_enquadramento_options().keys())).pack(pady=5)

        ttk.Label(config_frame, text="Modulação Digital:").pack(pady=5)
        ttk.OptionMenu(config_frame, self.mod_digital_type_var,
                       self.mod_digital_type_var.get(),
                       *list(self.simulador.get_mod_digital_options().keys())).pack(pady=5)

        ttk.Label(config_frame, text="Modulação por Portadora:").pack(pady=5)
        ttk.OptionMenu(config_frame, self.mod_portadora_type_var,
                       self.mod_portadora_type_var.get(),
                       *list(self.simulador.get_mod_portadora_options().keys())).pack(pady=5)

        ttk.Label(config_frame, text="Detecção de Erros:").pack(pady=5)
        ttk.OptionMenu(config_frame, self.detecao_erro_type_var,
                       self.detecao_erro_type_var.get(),
                       *list(self.simulador.get_deteccao_erro_options().keys())).pack(pady=5)

        ttk.Label(config_frame, text="Correção de Erros:").pack(pady=5)
        ttk.OptionMenu(config_frame, self.correcao_erro_type_var,
                       self.correcao_erro_type_var.get(),
                       *list(self.simulador.get_correcao_erro_options().keys())).pack(pady=5)

        ttk.Label(config_frame, text="Taxa de Erros (0.0 a 0.1):").pack(pady=5)
        ttk.Scale(config_frame, from_=0.0, to_=0.1, orient=tk.HORIZONTAL,
                  variable=self.taxa_erros_var, # REMOVIDO "resolution=0.001"
                  command=self._update_taxa_erros_label).pack(pady=5, fill=tk.X)
        self.taxa_erros_label = ttk.Label(config_frame, text=f"Atual: {self.taxa_erros_var.get():.3f}")
        self.taxa_erros_label.pack()

        ttk.Button(config_frame, text="Simular", command=self.run_simulation).pack(pady=20)

        # Frame de Resultados e Gráficos (Direita)
        results_frame = ttk.Frame(main_frame, padding="10")
        results_frame.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")
        main_frame.grid_columnconfigure(1, weight=3) # Gráficos maiores

        # Notebook para organizar as saídas e gráficos
        self.notebook = ttk.Notebook(results_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        # Aba de Saídas de Texto
        text_output_tab = ttk.Frame(self.notebook)
        self.notebook.add(text_output_tab, text="Saídas de Texto")

        ttk.Label(text_output_tab, text="Bits Transmitidos (Após Enlace Tx):").pack(pady=5)
        self.tx_output_text = tk.Text(text_output_tab, wrap=tk.WORD, height=5, width=80)
        self.tx_output_text.pack(fill=tk.X, expand=True)
        self.tx_output_text.config(state=tk.DISABLED) # Somente leitura

        ttk.Label(text_output_tab, text="Bits Recebidos (Após Enlace Rx):").pack(pady=5)
        self.rx_output_bits_text = tk.Text(text_output_tab, wrap=tk.WORD, height=5, width=80)
        self.rx_output_bits_text.pack(fill=tk.X, expand=True)
        self.rx_output_bits_text.config(state=tk.DISABLED)

        ttk.Label(text_output_tab, text="Texto Recebido (Aplicação Rx):").pack(pady=5)
        self.rx_output_final_text = tk.Text(text_output_tab, wrap=tk.WORD, height=5, width=80)
        self.rx_output_final_text.pack(fill=tk.X, expand=True)
        self.rx_output_final_text.config(state=tk.DISABLED)


        # Aba de Gráficos de Sinais
        self.plot_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.plot_tab, text="Gráficos de Sinais")

        self.fig, self.ax = plt.subplots(figsize=(10, 6)) # Aumenta o tamanho da figura
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.plot_tab)
        self.canvas_widget = self.canvas.get_tk_widget()
        self.canvas_widget.pack(fill=tk.BOTH, expand=True)

        self.toolbar = NavigationToolbar2Tk(self.canvas, self.plot_tab)
        self.toolbar.update()
        self.canvas_widget.pack(fill=tk.BOTH, expand=True)

        self.clear_plot() # Limpa o gráfico inicial

    def _update_taxa_erros_label(self, val):
        self.taxa_erros_label.config(text=f"Atual: {float(val):.3f}")

    def clear_plot(self):
        self.ax.clear()
        self.ax.set_title("Gráfico de Sinais (Transmissor)")
        self.ax.set_xlabel("Tempo / Amostras")
        self.ax.set_ylabel("Amplitude")
        self.ax.grid(True)
        self.canvas.draw()

    def update_text_output(self, tx_bits, rx_bits, rx_text):
        self.tx_output_text.config(state=tk.NORMAL)
        self.tx_output_text.delete(1.0, tk.END)
        self.tx_output_text.insert(tk.END, tx_bits)
        self.tx_output_text.config(state=tk.DISABLED)

        self.rx_output_bits_text.config(state=tk.NORMAL)
        self.rx_output_bits_text.delete(1.0, tk.END)
        self.rx_output_bits_text.insert(tk.END, rx_bits)
        self.rx_output_bits_text.config(state=tk.DISABLED)

        self.rx_output_final_text.config(state=tk.NORMAL)
        self.rx_output_final_text.delete(1.0, tk.END)
        self.rx_output_final_text.insert(tk.END, rx_text)
        self.rx_output_final_text.config(state=tk.DISABLED)


    def run_simulation(self):
        input_text = self.text_input_var.get()
        config = {
            'tipo_enquadramento': self.enquadramento_type_var.get(),
            'tipo_modulacao_digital': self.mod_digital_type_var.get(),
            'tipo_modulacao_portadora': self.mod_portadora_type_var.get(),
            'tipo_detecao_erro': self.detecao_erro_type_var.get(),
            'tipo_correcao_erro': self.correcao_erro_type_var.get(),
            'taxa_erros': self.taxa_erros_var.get()
        }

        # Chamar o método de simulação do SimuladorRedes
        try:
            tx_bits_output, rx_bits_output, rx_text_output, signal_plot_data = \
                self.simulador.simular_transmissao_receptor(input_text, config)

            self.update_text_output(tx_bits_output, rx_bits_output, rx_text_output)

            # Atualizar gráfico
            self.ax.clear()
            self.ax.plot(signal_plot_data)
            self.ax.set_title(f"Sinal Modulado Tx ({config['tipo_modulacao_digital']} + {config['tipo_modulacao_portadora']})")
            self.ax.set_xlabel("Amostras do Sinal")
            self.ax.set_ylabel("Amplitude")
            self.ax.grid(True)
            self.canvas.draw()
            self.notebook.select(self.plot_tab) # Mudar para a aba do gráfico
            
            messagebox.showinfo("Simulação Concluída", "A simulação foi executada com sucesso!")

        except ValueError as e:
            messagebox.showerror("Erro de Simulação", str(e))
        except Exception as e:
            messagebox.showerror("Erro Inesperado", f"Ocorreu um erro: {e}")

if __name__ == "__main__":
    root = tk.Tk()
    app = NetworkSimulatorGUI(root)
    root.mainloop()