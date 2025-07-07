import tkinter as tk
from tkinter import ttk, scrolledtext
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import numpy as np
import threading
import queue
import sys

sys.path.append('../')
from Simulador import receptor

class ReceptorGUI(ttk.Frame):
    def __init__(self, master):
        super().__init__(master, padding="10")
        self.master = master
        self.master.title("Simulador de Transmissão - Receptor (Rx)")
        self.master.geometry("1200x800")
        self.pack(fill=tk.BOTH, expand=True)

        self.update_queue = queue.Queue()
        self._create_variables()
        self._create_widgets()

        self.start_listening_thread()
        self.process_queue()

    def _create_variables(self):
        self.connection_status_var = tk.StringVar(value="Iniciando...")
        self.decode_status_var = tk.StringVar(value="Inativo")
        self.detection_method_var = tk.StringVar(value="Detecção:")
        self.detection_status_var = tk.StringVar(value="N/A")
        self.detection_details_var = tk.StringVar(value="")
        self.hamming_status_var = tk.StringVar(value="N/A")
        self.received_enquadramento_var = tk.StringVar(value="N/A")
        self.received_mod_digital_var = tk.StringVar(value="N/A")
        self.received_mod_portadora_var = tk.StringVar(value="N/A")
        self.received_detecao_erro_var = tk.StringVar(value="N/A")
        self.received_correcao_erro_var = tk.StringVar(value="N/A")
        self.received_bit_rate_var = tk.StringVar(value="N/A")
        self.received_freq_var = tk.StringVar(value="N/A")
        self.received_amplitude_var = tk.StringVar(value="N/A")
        self.received_sampling_rate_var = tk.StringVar(value="N/A")
        self.received_error_rate_var = tk.StringVar(value="N/A")

    def _create_widgets(self):
        self.grid_columnconfigure(0, weight=1, minsize=450)
        self.grid_columnconfigure(1, weight=2)
        self.grid_rowconfigure(0, weight=1)

        left_panel = ttk.Frame(self)
        left_panel.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

        received_config_frame = ttk.LabelFrame(left_panel, text="Configurações Recebidas", padding="10")
        received_config_frame.pack(fill=tk.X, pady=5)
        received_config_frame.grid_columnconfigure(1, weight=1)
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
        for i, (label, var) in enumerate(configs):
            ttk.Label(received_config_frame, text=label).grid(row=i, column=0, sticky="w", padx=2, pady=1)
            ttk.Label(received_config_frame, textvariable=var, foreground="#333").grid(row=i, column=1, sticky="w", padx=2, pady=1)

        status_process_frame = ttk.LabelFrame(left_panel, text="Status do Processamento", padding="10")
        status_process_frame.pack(fill=tk.X, pady=10)
        status_process_frame.grid_columnconfigure(1, weight=1)
        self.connection_status_label = self.create_status_row(status_process_frame, 0, "Status Conexão:", self.connection_status_var)
        self.decode_status_label = self.create_status_row(status_process_frame, 1, "Status Decodificação:", self.decode_status_var)
        self.hamming_status_label = self.create_status_row(status_process_frame, 2, "Status Hamming:", self.hamming_status_var)

        self.detection_method_label = ttk.Label(status_process_frame, textvariable=self.detection_method_var)
        self.detection_method_label.grid(row=3, column=0, sticky="w", padx=2, pady=1)
        self.detection_status_label = ttk.Label(status_process_frame, textvariable=self.detection_status_var)
        self.detection_status_label.grid(row=3, column=1, sticky="w", padx=2, pady=1)
        self.detection_details_label = ttk.Label(status_process_frame, textvariable=self.detection_details_var, font=('TkFixedFont', 8), wraplength=350)
        self.detection_details_label.grid(row=4, column=0, columnspan=2, sticky="w", padx=2, pady=1)

        received_msg_frame = ttk.LabelFrame(left_panel, text="Mensagem Final Recebida", padding="10")
        received_msg_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        self.received_message_text = scrolledtext.ScrolledText(received_msg_frame, wrap=tk.WORD, height=4, state="disabled", font=("Helvetica", 12))
        self.received_message_text.pack(fill=tk.BOTH, expand=True)

        plot_container_frame = ttk.LabelFrame(self, text="Gráficos do Sinal Recebido", padding="10")
        plot_container_frame.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")
        self.plot_notebook = ttk.Notebook(plot_container_frame)
        self.plot_notebook.pack(fill=tk.BOTH, expand=True)

        self.ax_pre, self.canvas_pre = self.create_plot_tab("Sinal RX")
        self.ax_post, self.canvas_post = self.create_plot_tab("Bits RX")
        self.ax_err, self.canvas_err = self.create_plot_tab("Erros no Canal")
        self.ax_corrigidos, self.canvas_corrigidos = self.create_plot_tab("Bits Corrigidos")
        self.ax_err_corrigidos, self.canvas_err_corrigidos = self.create_plot_tab("Erros Após Correção")

    def create_plot_tab(self, name):
        tab = ttk.Frame(self.plot_notebook)
        self.plot_notebook.add(tab, text=name)
        fig, ax = plt.subplots(figsize=(6, 3))
        canvas = FigureCanvasTkAgg(fig, master=tab)
        toolbar = NavigationToolbar2Tk(canvas, tab)
        toolbar.update()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        self.clear_plot_ax(ax, canvas, title=name)
        return ax, canvas

    def clear_plot_ax(self, ax, canvas, title):
        ax.clear()
        ax.set_title(title, fontsize=10)
        ax.grid(True, linestyle='--', linewidth=0.5)
        canvas.draw()

    def plot_pre_demod(self, data):
        ax, canvas = self.ax_pre, self.canvas_pre
        self.clear_plot_ax(ax, canvas, "Sinal Recebido no Canal")
        ax.plot(data['t'], data['signal_real'], color='coral', linewidth=1)
        ax.set_xlabel("Tempo (s)")
        ax.set_ylabel("Amplitude")
        canvas.draw()

    def plot_post_demod(self, data):
        ax, canvas = self.ax_post, self.canvas_post
        config = data['config']
        self.clear_plot_ax(ax, canvas, f"Bits Recuperados ({config['mod_digital_type']})")
        ax.step(data['t'], data['signal'], where='post', color='dodgerblue', linewidth=1.2)
        ax.set_xlabel("Tempo (s)")
        ax.set_ylabel("Nível Lógico")
        ax.set_ylim(-1.5, 1.5)
        canvas.draw()

    def plot_error(self, data):
        ax, canvas = self.ax_err, self.canvas_err
        self.clear_plot_ax(ax, canvas, "Comparação de Bits com Erros")
        min_len = min(len(data['ideal_bits']), len(data['received_bits']))
        ideal = np.array(data['ideal_bits'][:min_len])
        received = np.array(data['received_bits'][:min_len])
        t = data['t_ideal'][:min_len]
        errors = np.where(ideal != received)[0]
        ax.step(t, ideal, where='post', color='blue', label='Bits Ideais (TX)', lw=0.8)
        ax.step(t, received, where='post', color='green', linestyle='--', label='Bits RX', lw=0.8)
        if len(errors) > 0:
            ax.plot(t[errors], received[errors] + 0.1, 'ro', markersize=4, label=f'{len(errors)} Erros')
        ax.set_xlabel("Tempo (s)")
        ax.set_ylabel("Valor")
        ax.legend(fontsize='small')
        canvas.draw()

    def plot_corrected_bits(self, data):
        ax, canvas = self.ax_corrigidos, self.canvas_corrigidos
        config = data['config']
        self.clear_plot_ax(ax, canvas, f"Bits Corrigidos ({config['mod_digital_type']})")
        ax.step(data['t'], data['signal'], where='post', color='purple', linewidth=1.2)
        ax.set_xlabel("Tempo (s)")
        ax.set_ylabel("Nível Lógico")
        ax.set_ylim(-1.5, 1.5)
        canvas.draw()

    def plot_error_corrected(self, data):
        ax, canvas = self.ax_err_corrigidos, self.canvas_err_corrigidos
        self.clear_plot_ax(ax, canvas, "Erros Após Correção")
        min_len = min(len(data['ideal_bits']), len(data['corrected_bits']))
        ideal = np.array(data['ideal_bits'][:min_len])
        corrected = np.array(data['corrected_bits'][:min_len])
        t = data['t_ideal'][:min_len]
        errors = np.where(ideal != corrected)[0]
        ax.step(t, ideal, where='post', color='blue', label='Bits Ideais (TX)', lw=0.8)
        ax.step(t, corrected, where='post', color='purple', linestyle='--', label='Bits Corrigidos (RX)', lw=0.8)
        if len(errors) > 0:
            ax.plot(t[errors], corrected[errors] + 0.1, 'ro', markersize=4, label=f'{len(errors)} Erros')
        ax.set_xlabel("Tempo (s)")
        ax.set_ylabel("Valor")
        ax.legend(fontsize='small')
        canvas.draw()

    def process_queue(self):
        try:
            while not self.update_queue.empty():
                msg = self.update_queue.get_nowait()
                msg_type = msg.get('type')
                if msg_type == 'new_connection':
                    self.clear_all_for_new_connection(msg['address'])
                elif msg_type == 'connection_status':
                    self.update_status_var(self.connection_status_label, self.connection_status_var, msg)
                elif msg_type == 'decode_status':
                    self.update_status_var(self.decode_status_label, self.decode_status_var, msg)
                elif msg_type == 'hamming_status':
                    self.update_status_var(self.hamming_status_label, self.hamming_status_var, msg)
                elif msg_type == 'received_configs':
                    self.update_received_configs(msg['data'])
                elif msg_type == 'detection_result':
                    self.update_detection_display(msg['data'])
                elif msg_type == 'final_message':
                    self.update_received_message(msg['message'])
                elif msg_type == 'plot':
                    self.dispatch_plot(msg['tab'], msg['data'])
        finally:
            self.master.after(100, self.process_queue)

    def update_detection_display(self, data):
        method = data.get('method')
        status = data.get('status')
        color = "green" if "OK" in status else "red" if "INVÁLIDO" in status else "black"
        self.detection_details_var.set("")
        if method == "Nenhuma":
            self.detection_method_var.set("Detecção de Erro:")
            self.detection_status_var.set("N/A (desativada)")
            self.detection_status_label.config(foreground="black")
        elif method == "Paridade Par":
            self.detection_method_var.set("Status Paridade:")
            self.detection_status_var.set(status)
            self.detection_status_label.config(foreground=color)
        elif method == "CRC-32":
            self.detection_method_var.set("Status CRC-32:")
            self.detection_status_var.set(status)
            self.detection_status_label.config(foreground=color)
            calc = data.get('calc')
            recv = data.get('recv')
            details_text = f"Calculado: 0b{calc:032b}\nRecebido:  0b{recv:032b}"
            self.detection_details_var.set(details_text)

    def clear_all_for_new_connection(self, address):
        self.connection_status_var.set(f"Conexão de {address}")
        self.connection_status_label.config(foreground='green')
        for var in [self.decode_status_var, self.detection_status_var, self.hamming_status_var,
                    self.received_enquadramento_var, self.received_mod_digital_var,
                    self.received_mod_portadora_var, self.received_detecao_erro_var,
                    self.received_correcao_erro_var, self.received_bit_rate_var,
                    self.received_freq_var, self.received_amplitude_var,
                    self.received_sampling_rate_var, self.received_error_rate_var]:
            var.set("...")
        self.detection_method_var.set("Detecção:")
        self.detection_details_var.set("")
        self.received_message_text.config(state="normal")
        self.received_message_text.delete(1.0, tk.END)
        self.received_message_text.config(state="disabled")
        for ax, canvas, title in [
            (self.ax_pre, self.canvas_pre, "Sinal RX"),
            (self.ax_post, self.canvas_post, "Bits RX"),
            (self.ax_err, self.canvas_err, "Erros no Canal"),
            (self.ax_corrigidos, self.canvas_corrigidos, "Bits Corrigidos"),
            (self.ax_err_corrigidos, self.canvas_err_corrigidos, "Erros Após Correção")
        ]:
            self.clear_plot_ax(ax, canvas, title)

    def create_status_row(self, parent, row, text, var):
        ttk.Label(parent, text=text).grid(row=row, column=0, sticky="w", padx=2, pady=1)
        label = ttk.Label(parent, textvariable=var)
        label.grid(row=row, column=1, sticky="w", padx=2, pady=1)
        return label

    def start_listening_thread(self):
        thread = threading.Thread(target=receptor.run_receiver, args=(self.gui_update_callback,))
        thread.daemon = True
        thread.start()

    def gui_update_callback(self, msg):
        self.update_queue.put(msg)

    def update_status_var(self, label, var, msg):
        var.set(msg['message'])
        label.config(foreground=msg['color'])

    def dispatch_plot(self, tab, data):
        if tab == 'pre_demod': self.plot_pre_demod(data)
        elif tab == 'post_demod': self.plot_post_demod(data)
        elif tab == 'error': self.plot_error(data)
        elif tab == 'corrected_bits': self.plot_corrected_bits(data)
        elif tab == 'error_corrected': self.plot_error_corrected(data)

    def update_received_configs(self, data):
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
        self.received_message_text.config(state="normal")
        self.received_message_text.delete(1.0, tk.END)
        self.received_message_text.insert(tk.END, message)
        self.received_message_text.config(state="disabled")

if __name__ == '__main__':
    root = tk.Tk()
    app = ReceptorGUI(root)
    root.mainloop()
