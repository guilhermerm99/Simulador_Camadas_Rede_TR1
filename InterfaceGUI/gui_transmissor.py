import tkinter as tk
from tkinter import ttk, scrolledtext
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np
import threading
import queue
import sys

sys.path.append('../')
from Simulador import transmissor

class TransmissorGUI(ttk.Frame):
    def __init__(self, master):
        """
        Inicializa a GUI do transmissor, configurando janela, variáveis de controle,
        widgets e o loop de processamento da fila de mensagens assíncronas.
        """
        super().__init__(master, padding="10")
        self.master = master
        self.master.title("Simulador de Transmissão - Transmissor (Tx)")
        self.master.geometry("1100x750")
        self.pack(fill=tk.BOTH, expand=True)

        self.update_queue = queue.Queue()  # Fila para comunicação segura entre threads

        # --- Variáveis de Controle da Interface ---
        self.msg_var = tk.StringVar(value="Ola mundo! 03/07/2025")          # Mensagem a ser transmitida
        self.enquadramento_var = tk.StringVar(value='Bit Stuffing (Flags)') # Método de enquadramento
        self.mod_digital_var = tk.StringVar(value='NRZ-Polar')              # Tipo de modulação digital
        self.mod_portadora_var = tk.StringVar(value='ASK')                  # Tipo de modulação da portadora
        self.detecao_erro_var = tk.StringVar(value='CRC-32')                # Método de detecção de erro
        self.correcao_erro_var = tk.StringVar(value='Hamming')              # Método de correção de erro
        self.taxa_erros_var = tk.DoubleVar(value=0.01)                      # Taxa de erros simulada no canal

        self._create_widgets()
        self.process_queue()  # Inicia o loop de verificação da fila de mensagens

    def _create_widgets(self):
        """
        Cria e posiciona todos os widgets da interface:
        controles à esquerda e área de gráficos à direita.
        """
        # Configuração do grid principal com duas colunas e uma linha
        self.grid_columnconfigure(0, weight=1, minsize=400)  # Painel esquerdo
        self.grid_columnconfigure(1, weight=2)               # Painel direito (gráficos)
        self.grid_rowconfigure(0, weight=1)

        # --- Painel Esquerdo: Controles e Status ---
        left_panel = ttk.Frame(self)
        left_panel.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

        # Frame para configurações da simulação (dropdowns, entrada de texto, etc)
        config_frame = ttk.LabelFrame(left_panel, text="Configurações da Simulação", padding="10")
        config_frame.pack(fill=tk.X, pady=5)
        config_frame.grid_columnconfigure(1, weight=1)

        # Opções possíveis para os comboboxes
        enquadramento_options = ["Contagem de caracteres", "Byte Stuffing (Flags)", "Bit Stuffing (Flags)"]
        detecao_erro_options = ["Nenhuma", "Paridade Par", "CRC-32"]
        correcao_erro_options = ["Nenhuma", "Hamming"]
        mod_digital_options = ["NRZ-Polar", "Manchester", "Bipolar"]
        mod_portadora_options = ["ASK", "FSK", "8-QAM"]

        # Cria linhas de controle com label + widget (Entry ou Combobox)
        self.create_control_row(config_frame, 0, "Mensagem:", ttk.Entry(config_frame, textvariable=self.msg_var))
        self.create_control_row(config_frame, 1, "Enquadramento:", ttk.Combobox(config_frame, textvariable=self.enquadramento_var, values=enquadramento_options, state="readonly"))
        self.create_control_row(config_frame, 2, "Mod. Digital:", ttk.Combobox(config_frame, textvariable=self.mod_digital_var, values=mod_digital_options, state="readonly"))
        self.create_control_row(config_frame, 3, "Mod. Portadora:", ttk.Combobox(config_frame, textvariable=self.mod_portadora_var, values=mod_portadora_options, state="readonly"))
        self.create_control_row(config_frame, 4, "Detecção de Erro:", ttk.Combobox(config_frame, textvariable=self.detecao_erro_var, values=detecao_erro_options, state="readonly"))
        self.create_control_row(config_frame, 5, "Correção de Erro:", ttk.Combobox(config_frame, textvariable=self.correcao_erro_var, values=correcao_erro_options, state="readonly"))

        # Controle deslizante para taxa de erro no canal
        ttk.Label(config_frame, text="Taxa de Erros no Canal:").grid(row=6, column=0, sticky="w", padx=5, pady=(10,0))
        error_scale = ttk.Scale(
            config_frame, from_=0.0, to_=0.1, orient=tk.HORIZONTAL,
            variable=self.taxa_erros_var,
            command=lambda v: self.error_label.config(text=f"{float(v):.3f}")
        )
        error_scale.grid(row=7, column=0, columnspan=2, sticky="ew", padx=5)
        self.error_label = ttk.Label(config_frame, text=f"{self.taxa_erros_var.get():.3f}")
        self.error_label.grid(row=8, column=0, columnspan=2, sticky="w", padx=5)

        # Botão para iniciar transmissão
        self.send_button = ttk.Button(left_panel, text="Iniciar Transmissão", command=self.start_transmission_thread)
        self.send_button.pack(fill=tk.X, pady=20)
        
        # Área para exibir status e mensagens do transmissor
        status_frame = ttk.LabelFrame(left_panel, text="Status", padding=10)
        status_frame.pack(fill=tk.BOTH, expand=True)
        self.status_label = ttk.Label(status_frame, text="Pronto.", foreground="blue", wraplength=380)
        self.status_label.pack(fill=tk.BOTH, expand=True)

        # --- Painel Direito: Área de Gráficos ---
        plot_container = ttk.LabelFrame(self, text="Gráficos do Sinal Transmitido", padding="10")
        plot_container.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")

        # Notebook para múltiplas abas de gráficos
        self.plot_notebook = ttk.Notebook(plot_container)
        self.plot_notebook.pack(fill=tk.BOTH, expand=True)

        # Cria abas para os diferentes gráficos
        self.ax_digital, self.canvas_digital = self.create_plot_tab("Sinal Digital")
        self.ax_analog, self.canvas_analog = self.create_plot_tab("Sinal Modulado")
        self.ax_const, self.canvas_const = self.create_plot_tab("Constelação")

    def create_control_row(self, parent, row, label_text, widget):
        """
        Cria uma linha com label e widget no grid do pai.
        """
        ttk.Label(parent, text=label_text).grid(row=row, column=0, sticky="w", padx=5, pady=2)
        widget.grid(row=row, column=1, sticky="ew", padx=5, pady=2)

    def create_plot_tab(self, tab_name):
        """
        Cria uma aba no notebook com um gráfico matplotlib embutido.
        Retorna o eixo e o canvas para atualizações futuras.
        """
        tab = ttk.Frame(self.plot_notebook)
        self.plot_notebook.add(tab, text=tab_name)
        fig, ax = plt.subplots(figsize=(10, 3))
        plt.tight_layout()
        canvas = FigureCanvasTkAgg(fig, master=tab)
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        self.clear_plot_ax(ax, canvas, title=tab_name)
        return ax, canvas

    def start_transmission_thread(self):
        """
        Inicia thread para rodar a transmissão assincronamente,
        desabilita botão para evitar múltiplas execuções simultâneas
        e limpa gráficos antes de começar.
        """
        self.send_button.config(state="disabled")
        self.clear_all()
        
        # Parâmetros coletados dos controles da GUI
        params = {
            "message": self.msg_var.get(),
            "enquadramento_type": self.enquadramento_var.get(),
            "mod_digital_type": self.mod_digital_var.get(),
            "mod_portadora_type": self.mod_portadora_var.get(),
            "detecao_erro_type": self.detecao_erro_var.get(),
            "correcao_erro_type": self.correcao_erro_var.get(),
            "taxa_erros": self.taxa_erros_var.get()
        }
        
        # Cria e inicia thread daemon para transmissão
        thread = threading.Thread(target=transmissor.run_transmitter, args=(params, self.gui_update_callback))
        thread.daemon = True
        thread.start()

    def gui_update_callback(self, update_dict):
        """
        Callback para a thread do transmissor colocar mensagens na fila da GUI
        de forma thread-safe.
        """
        self.update_queue.put(update_dict)

    def process_queue(self):
        """
        Processa mensagens da fila de updates enviadas pela thread do transmissor.
        Atualiza status, gráficos e habilita botão conforme necessário.
        É chamado periodicamente via after.
        """
        try:
            while not self.update_queue.empty():
                msg = self.update_queue.get_nowait()
                msg_type = msg.get('type')

                if msg_type == 'status':
                    # Atualiza label de status com mensagem e cor
                    self.status_label.config(text=msg['message'], foreground=msg['color'])
                    # Reabilita botão se transmissão terminou ou houve erro
                    if "concluída" in msg['message'] or "Erro" in msg['message']:
                        self.send_button.config(state="normal")

                elif msg_type == 'log':
                    # Logs de console são ignorados na GUI do transmissor
                    pass

                elif msg_type == 'plot_digital':
                    self.update_digital_plot(msg['data'])

                elif msg_type == 'plot_analog':
                    self.update_analog_plot(msg['data'])

                elif msg_type == 'plot_constellation':
                    self.update_constellation_plot(msg['data'])

        finally:
            # Agenda a próxima verificação da fila em 100ms
            self.master.after(100, self.process_queue)

    def clear_all(self):
        """
        Limpa todos os gráficos para reiniciar visualização.
        """
        self.clear_plot_ax(self.ax_digital, self.canvas_digital, "Sinal Digital")
        self.clear_plot_ax(self.ax_analog, self.canvas_analog, "Sinal Modulado")
        self.clear_plot_ax(self.ax_const, self.canvas_const, "Constelação")

    def clear_plot_ax(self, ax, canvas, title):
        """
        Limpa e prepara eixo do gráfico com título e grade.
        """
        ax.clear()
        ax.set_title(title, fontsize=10)
        ax.grid(True)
        plt.tight_layout()
        canvas.draw()

    def update_digital_plot(self, plot_data):
        """
        Atualiza gráfico do sinal digital (níveis lógicos) usando gráfico step.
        """
        ax, canvas = self.ax_digital, self.canvas_digital
        t, signal, config = plot_data['t'], plot_data['signal'], plot_data['config']
        self.clear_plot_ax(ax, canvas, f"Sinal Digital ({config['mod_digital_type']})")
        ax.step(t, signal, where='post')
        ax.set_xlabel("Tempo (s)")
        ax.set_ylabel("Nível")
        if len(signal) > 0:
            ax.set_ylim(min(signal)-0.5, max(signal)+0.5)
        canvas.draw()
        
    def update_analog_plot(self, plot_data):
        """
        Atualiza gráfico do sinal modulado no domínio do tempo.
        Ajusta o eixo x para mostrar até 20 bits transmitidos ou tempo total.
        """
        ax, canvas = self.ax_analog, self.canvas_analog
        t, signal, config = plot_data['t'], plot_data['signal'], plot_data['config']
        self.clear_plot_ax(ax, canvas, f"Sinal Modulado ({config['mod_portadora_type']})")
        ax.plot(t, signal)
        ax.set_xlabel("Tempo (s)")
        ax.set_ylabel("Amplitude")
        if len(t) > 0:
            display_duration = min(t[-1], 20 / config['bit_rate'])
            ax.set_xlim(0, display_duration)
        canvas.draw()

    def update_constellation_plot(self, plot_data):
        """
        Atualiza gráfico da constelação 8-QAM, exibindo pontos no plano I-Q.
        """
        ax, canvas = self.ax_const, self.canvas_const
        points = plot_data['points']
        self.clear_plot_ax(ax, canvas, "Constelação 8-QAM (TX)")
        ax.scatter([p.real for p in points], [p.imag for p in points], marker='o')
        ax.axhline(0, color='grey', lw=0.5)
        ax.axvline(0, color='grey', lw=0.5)
        ax.set_xlabel("Em Fase (I)")
        ax.set_ylabel("Quadratura (Q)")
        canvas.draw()
        
if __name__ == '__main__':
    root = tk.Tk()
    app = TransmissorGUI(root)
    root.mainloop()
