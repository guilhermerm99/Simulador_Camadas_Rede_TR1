# Simulador/transmissor.py

import socket, sys, numpy as np, time, base64
sys.path.append('../')
from Utilidades import utils
from CamadaEnlace.deteccao_erros import ErrorDetector
from CamadaEnlace.correcao_erros import ErrorCorrector
from CamadaEnlace.enquadramento import Framer
from CamadaFisica.modulacoes_digitais import DigitalEncoder
from CamadaFisica.modulacoes_portadora import CarrierModulator

HOST = '127.0.0.1'; PORT = 65432

def format_log(data_str, max_len=64):
    if len(data_str) > max_len: return f"{data_str[:(max_len-3)//2]}...{data_str[-(max_len-3)//2:]}"
    return data_str

def run_transmitter(params, update_callback):
    try:
        config = { 
            "message": params.get("message"), 
            "enquadramento_type": params.get("enquadramento_type"), 
            "mod_digital_type": params.get("mod_digital_type"), 
            "mod_portadora_type": params.get("mod_portadora_type"), 
            "detecao_erro_type": params.get("detecao_erro_type"), 
            "correcao_erro_type": params.get("correcao_erro_type"), 
            "taxa_erros": params.get("taxa_erros", 0.0), 
            "bit_rate": 1000, 
            "freq_base": 5000, 
            "amplitude": 1.0 
        }
        config["sampling_rate"] = config["bit_rate"] * 20
        error_detector, error_corrector, framer = ErrorDetector(), ErrorCorrector(), Framer()
        digital_encoder = DigitalEncoder()
        modulator = CarrierModulator(config["bit_rate"], config["freq_base"], config["amplitude"], config["sampling_rate"])

        log_msg = "--- INÍCIO DA TRANSMISSÃO ---"
        update_callback({'type': 'status', 'message': log_msg, 'color': 'black'})
        print(log_msg)

        bits = utils.text_to_binary(config['message'])
        bits_para_enlace = bits
        if config["correcao_erro_type"] == "Hamming":
            bits_para_enlace = error_corrector.encode_hamming(bits)

        detecao_selecionada = config["detecao_erro_type"]
        if detecao_selecionada == "CRC-32":
            bits_para_enlace += error_detector.generate_crc(bits_para_enlace)
        elif detecao_selecionada == "Paridade Par":
            if len(bits_para_enlace) % 8 != 0:
                bits_para_enlace += '0' * (8 - len(bits_para_enlace) % 8)
            bytes_com_paridade = [error_detector.add_even_parity(bits_para_enlace[i:i+8]) for i in range(0, len(bits_para_enlace), 8)]
            bits_para_enlace = "".join(bytes_com_paridade)

        config['original_payload_len'] = len(bits_para_enlace)

        enquadramento_selecionado = config["enquadramento_type"]
        if enquadramento_selecionado == "Contagem de caracteres":
            frame = framer.frame_char_count(bits_para_enlace)
        elif enquadramento_selecionado == "Byte Stuffing (Flags)":
            frame = framer.frame_byte_stuffing(bits_para_enlace)
        else:
            frame = framer.frame_bit_stuffing(bits_para_enlace)

        bits_transmitidos = frame
        bits_transmitidos_b64 = base64.b64encode(bits_transmitidos.encode('utf-8')).decode('utf-8')
        config['bits_transmitidos_b64'] = bits_transmitidos_b64

        digital_signal = digital_encoder.encode(frame, config["mod_digital_type"])
        update_callback({'type': 'plot_digital', 'data': {'t': np.arange(len(digital_signal)) * (1.0 / config["bit_rate"]), 'signal': digital_signal, 'config': config}})

        signal_source = frame if config["mod_portadora_type"] == "8-QAM" else digital_signal
        t_analog, analog_signal, *qam_points = modulator.modulate(signal_source, config["mod_portadora_type"])
        update_callback({'type': 'plot_analog', 'data': {'t': t_analog, 'signal': analog_signal, 'config': config}})
        if qam_points:
            update_callback({'type': 'plot_constellation', 'data': {'points': qam_points[0]}})

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((HOST, PORT))
            metadata_keys = [
                "message", "enquadramento_type", "mod_digital_type", "mod_portadora_type",
                "detecao_erro_type", "correcao_erro_type", "taxa_erros", "bit_rate",
                "freq_base", "amplitude", "sampling_rate", "original_payload_len",
                "bits_transmitidos_b64"
            ]
            metadata = "|".join(str(config.get(k, '')) for k in metadata_keys)
            s.sendall(metadata.encode('utf-8'))
            time.sleep(0.1)
            s.sendall(analog_signal.astype(np.float32).tobytes())
            update_callback({'type': 'status', 'message': 'Transmissão concluída!', 'color': 'green'})

    except Exception as e:
        update_callback({'type': 'status', 'message': f"Erro crítico: {e}", 'color': 'red'})
