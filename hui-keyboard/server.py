from flask import Flask, request, jsonify, send_file
import socket
import struct
import json

app = Flask(__name__)

# Konfiguracja I2C
I2C_SOCKET = "/dev/i2c/hui.sock"
RPI_HOST = "rpi"
I2C_ADDRESS = 0x20


class HUIInterface:
    def __init__(self):
        self.key_buffer = []
        self.encoder_value = 0

    def send_i2c_data(self, data):
        """Wysyła dane przez symulowany I2C"""
        try:
            # Format: [adres, rejestr, dane...]
            packet = struct.pack('BB', I2C_ADDRESS, 0x00) + data

            # Wyślij przez socket
            with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as s:
                s.connect(I2C_SOCKET)
                s.send(packet)
        except Exception as e:
            print(f"I2C Error: {e}")


hui = HUIInterface()


@app.route('/')
def index():
    return send_file('index.html')


@app.route('/keypress', methods=['POST'])
def handle_keypress():
    data = request.json
    key = data.get('key')

    # Mapowanie klawiszy na kody
    key_map = {
        'F1': 0x01, 'F2': 0x02, 'F3': 0x03,
        'UP': 0x10, 'OK': 0x11, 'ESC': 0x12,
        'LEFT': 0x13, 'DOWN': 0x14, 'RIGHT': 0x15,
        'EMERGENCY': 0xFF, 'RESET': 0xFE,
        'ENCODER_CLICK': 0x20
    }

    if key in key_map:
        # Wyślij przez I2C
        hui.send_i2c_data(bytes([key_map[key]]))
        return jsonify({'status': 'ok'})

    return jsonify({'status': 'error', 'message': 'Unknown key'})


@app.route('/encoder', methods=['POST'])
def handle_encoder():
    data = request.json
    value = data.get('value', 0)

    hui.encoder_value = value

    # Wyślij wartość enkodera (rejestr 0x01)
    packet = struct.pack('BB', 0x01, value)
    hui.send_i2c_data(packet)

    return jsonify({'status': 'ok', 'value': value})


@app.route('/connect', methods=['POST'])
def connect():
    # Inicjalizacja połączenia
    return jsonify({'status': 'connected', 'address': f'0x{I2C_ADDRESS:02X}'})


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80)