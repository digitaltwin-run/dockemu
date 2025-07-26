import asyncio
import json
import socket
import struct
import threading
from datetime import datetime
from enum import Enum

from flask import Flask, jsonify, request
from flask_cors import CORS

# Import web interface routes at module level to avoid circular imports
from web_interface import web_app as web_blueprint

class ControlMode(Enum):
    NORMAL = 0x0000      # Bezpośrednia kontrola
    LINKAGE = 0x0001     # Połączenie DI->DO
    TOGGLE = 0x0002      # Przełączanie na zbocze
    EDGE_TRIGGER = 0x0003 # Zmiana na każde zbocze

class ModbusRTUIO8CH:
    """Symulator Modbus RTU IO 8CH zgodny z dokumentacją Waveshare"""
    
    def __init__(self, device_address=0x01):
        self.device_address = device_address
        self.baudrate = 9600
        
        # Stan urządzenia
        self.digital_inputs = [False] * 8
        self.digital_outputs = [False] * 8
        self.analog_inputs = [0.0] * 8
        self.analog_outputs = [0.0] * 8
        self.control_modes = [ControlMode.NORMAL] * 8
        
        # Rejestry flash
        self.flash_on_intervals = [0] * 8  # x100ms
        self.flash_off_intervals = [0] * 8
        self.flash_states = [False] * 8
        self.flash_timers = {}
        
        # Historia dla wizualizacji
        self.history = []
        self.max_history = 1000
        
        # TCP bridge dla łatwiejszego testowania
        self.tcp_bridge = None
        
    def calculate_crc16(self, data):
        """Oblicz CRC16 Modbus"""
        crc = 0xFFFF
        for byte in data:
            crc ^= byte
            for _ in range(8):
                if crc & 0x0001:
                    crc = (crc >> 1) ^ 0xA001
                else:
                    crc >>= 1
        return struct.pack('<H', crc)
    
    def process_modbus_frame(self, frame):
        """Przetwórz ramkę Modbus RTU"""
        if len(frame) < 4:
            return None
            
        # Sprawdź adres
        device_addr = frame[0]
        if device_addr != self.device_address and device_addr != 0x00:
            return None
            
        # Sprawdź CRC
        crc_received = frame[-2:]
        crc_calculated = self.calculate_crc16(frame[:-2])
        if crc_received != crc_calculated:
            return self.create_error_response(frame[0], frame[1], 0x01)
            
        # Przetwórz funkcję
        function_code = frame[1]
        
        if function_code == 0x01:  # Read Coils (outputs)
            return self.read_outputs(frame)
        elif function_code == 0x02:  # Read Discrete Inputs
            return self.read_inputs(frame)
        elif function_code == 0x03:  # Read Holding Registers
            return self.read_registers(frame)
        elif function_code == 0x05:  # Write Single Coil
            return self.write_single_output(frame)
        elif function_code == 0x06:  # Write Single Register
            return self.write_single_register(frame)
        elif function_code == 0x0F:  # Write Multiple Coils
            return self.write_multiple_outputs(frame)
        elif function_code == 0x10:  # Write Multiple Registers
            return self.write_multiple_registers(frame)
        else:
            return self.create_error_response(device_addr, function_code, 0x01)
    
    def read_outputs(self, frame):
        """Funkcja 0x01 - Odczyt stanu wyjść"""
        start_addr = struct.unpack('>H', frame[2:4])[0]
        count = struct.unpack('>H', frame[4:6])[0]
        
        if start_addr + count > 8:
            return self.create_error_response(frame[0], 0x01, 0x02)
            
        # Przygotuj odpowiedź
        byte_count = (count + 7) // 8
        response = bytearray([frame[0], 0x01, byte_count])
        
        # Pakuj bity
        output_byte = 0
        for i in range(count):
            if self.digital_outputs[start_addr + i]:
                output_byte |= (1 << (i % 8))
            if (i + 1) % 8 == 0 or i == count - 1:
                response.append(output_byte)
                output_byte = 0
                
        response += self.calculate_crc16(response)
        return bytes(response)
    
    def read_inputs(self, frame):
        """Funkcja 0x02 - Odczyt stanu wejść"""
        start_addr = struct.unpack('>H', frame[2:4])[0]
        count = struct.unpack('>H', frame[4:6])[0]
        
        if start_addr + count > 8:
            return self.create_error_response(frame[0], 0x02, 0x02)
            
        byte_count = (count + 7) // 8
        response = bytearray([frame[0], 0x02, byte_count])
        
        input_byte = 0
        for i in range(count):
            if self.digital_inputs[start_addr + i]:
                input_byte |= (1 << (i % 8))
            if (i + 1) % 8 == 0 or i == count - 1:
                response.append(input_byte)
                input_byte = 0
                
        response += self.calculate_crc16(response)
        return bytes(response)
    
    def write_single_output(self, frame):
        """Funkcja 0x05 - Zapis pojedynczego wyjścia"""
        addr = struct.unpack('>H', frame[2:4])[0]
        value = struct.unpack('>H', frame[4:6])[0]
        
        # Specjalne adresy
        if addr == 0x00FF:  # Kontrola wszystkich wyjść
            if value == 0xFF00:
                self.digital_outputs = [True] * 8
            elif value == 0x0000:
                self.digital_outputs = [False] * 8
            elif value == 0x5500:
                self.digital_outputs = [not state for state in self.digital_outputs]
            self.log_event("all_outputs", {"action": "control", "value": hex(value)})
            return frame  # Echo
            
        # Flash control
        if 0x0200 <= addr <= 0x0207:  # Flash ON
            channel = addr - 0x0200
            self.flash_on_intervals[channel] = value
            self.start_flash(channel)
            return frame
            
        if 0x0400 <= addr <= 0x0407:  # Flash OFF
            channel = addr - 0x0400
            self.flash_off_intervals[channel] = value
            return frame
            
        # Normalna kontrola wyjścia
        if addr < 8:
            if value == 0xFF00:
                self.digital_outputs[addr] = True
            elif value == 0x0000:
                self.digital_outputs[addr] = False
            elif value == 0x5500:
                self.digital_outputs[addr] = not self.digital_outputs[addr]
                
            self.log_event(f"output_{addr}", {
                "state": self.digital_outputs[addr],
                "mode": self.control_modes[addr].name
            })
            
            # Linkage mode
            if self.control_modes[addr] == ControlMode.LINKAGE:
                self.digital_outputs[addr] = self.digital_inputs[addr]
                
            return frame  # Echo odpowiedzi
        
        return self.create_error_response(frame[0], 0x05, 0x02)
    
    def read_registers(self, frame):
        """Funkcja 0x03 - Odczyt rejestrów"""
        start_addr = struct.unpack('>H', frame[2:4])[0]
        count = struct.unpack('>H', frame[4:6])[0]
        
        response = bytearray([frame[0], 0x03, count * 2])
        
        # Tryby kontroli (0x1000-0x1007)
        if 0x1000 <= start_addr < 0x1008:
            for i in range(count):
                addr = start_addr + i - 0x1000
                if addr < 8:
                    response += struct.pack('>H', self.control_modes[addr].value)
                    
        # Wersja software (0x8000)
        elif start_addr == 0x8000:
            response += struct.pack('>H', 0x00C8)  # V2.00
            
        # Adres urządzenia (0x4000)
        elif start_addr == 0x4000:
            response += struct.pack('>H', self.device_address)
            
        response += self.calculate_crc16(response)
        return bytes(response)
    
    def write_single_register(self, frame):
        """Funkcja 0x06 - Zapis pojedynczego rejestru"""
        addr = struct.unpack('>H', frame[2:4])[0]
        value = struct.unpack('>H', frame[4:6])[0]
        
        # Tryb kontroli
        if 0x1000 <= addr < 0x1008:
            channel = addr - 0x1000
            if value <= 3:
                self.control_modes[channel] = ControlMode(value)
                self.log_event(f"mode_{channel}", {"mode": ControlMode(value).name})
                
        # Zmiana baudrate (0x2000)
        elif addr == 0x2000:
            baudrates = [4800, 9600, 19200, 38400, 57600, 115200, 128000, 256000]
            if value & 0xFF < len(baudrates):
                self.baudrate = baudrates[value & 0xFF]
                
        # Zmiana adresu (0x4000)
        elif addr == 0x4000:
            if 0x01 <= value <= 0xFF:
                self.device_address = value
                
        return frame  # Echo
    
    def simulate_inputs(self, input_states):
        """Symuluj zmiany na wejściach"""
        for i, state in enumerate(input_states):
            prev_state = self.digital_inputs[i]
            self.digital_inputs[i] = state
            
            # Obsługa trybów
            if self.control_modes[i] == ControlMode.LINKAGE:
                self.digital_outputs[i] = state
            elif self.control_modes[i] == ControlMode.TOGGLE:
                if state and not prev_state:  # Rising edge
                    self.digital_outputs[i] = not self.digital_outputs[i]
            elif self.control_modes[i] == ControlMode.EDGE_TRIGGER:
                if state != prev_state:  # Any edge
                    self.digital_outputs[i] = not self.digital_outputs[i]
                    
        self.log_event("inputs", {"states": self.digital_inputs})
    
    def start_flash(self, channel):
        """Rozpocznij miganie wyjścia"""
        if channel in self.flash_timers:
            self.flash_timers[channel].cancel()
            
        def flash():
            if self.flash_states[channel]:
                # OFF phase
                self.digital_outputs[channel] = False
                interval = self.flash_off_intervals[channel] * 0.1
                self.flash_states[channel] = False
            else:
                # ON phase
                self.digital_outputs[channel] = True
                interval = self.flash_on_intervals[channel] * 0.1
                self.flash_states[channel] = True
                
            if interval > 0:
                self.flash_timers[channel] = threading.Timer(interval, flash)
                self.flash_timers[channel].start()
                
        flash()
    
    def log_event(self, event_type, data):
        """Zapisz zdarzenie do historii"""
        event = {
            "timestamp": datetime.now().isoformat(),
            "type": event_type,
            "data": data
        }
        self.history.append(event)
        if len(self.history) > self.max_history:
            self.history.pop(0)
    
    def create_error_response(self, addr, func, error_code):
        """Utwórz odpowiedź błędu"""
        response = bytearray([addr, func | 0x80, error_code])
        response += self.calculate_crc16(response)
        return bytes(response)
    
    def get_status(self):
        """Pobierz aktualny status urządzenia"""
        return {
            "device_address": self.device_address,
            "baudrate": self.baudrate,
            "digital_inputs": self.digital_inputs,
            "digital_outputs": self.digital_outputs,
            "control_modes": [mode.name for mode in self.control_modes],
            "flash_intervals": {
                "on": self.flash_on_intervals,
                "off": self.flash_off_intervals
            }
        }

# Flask Web API
app = Flask(__name__)
CORS(app)

simulator = ModbusRTUIO8CH()

# Register the web interface blueprint
app.register_blueprint(web_blueprint)

# Add CORS headers to all responses
@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response

@app.route('/api/status', methods=['GET'])
def get_status():
    """Pobierz status urządzenia"""
    return jsonify(simulator.get_status())

@app.route('/api/inputs', methods=['POST'])
def set_inputs():
    """Ustaw stany wejść (symulacja)"""
    data = request.json
    if 'states' in data and len(data['states']) == 8:
        simulator.simulate_inputs(data['states'])
        return jsonify({"status": "ok"})
    return jsonify({"error": "Invalid input data"}), 400

@app.route('/api/modbus', methods=['POST'])
def process_modbus():
    """Przetwórz ramkę Modbus"""
    data = request.json
    if 'frame' in data:
        frame = bytes.fromhex(data['frame'])
        response = simulator.process_modbus_frame(frame)
        if response:
            return jsonify({
                "response": response.hex(),
                "status": simulator.get_status()
            })
    return jsonify({"error": "Invalid frame"}), 400

@app.route('/api/history', methods=['GET'])
def get_history():
    """Pobierz historię zdarzeń"""
    limit = request.args.get('limit', 100, type=int)
    return jsonify(simulator.history[-limit:])

# TCP Bridge dla łatwiejszego testowania
class ModbusTCPBridge:
    def __init__(self, simulator, port=5020):
        self.simulator = simulator
        self.port = port
        self.server = None
        
    async def handle_client(self, reader, writer):
        """Obsługa klienta TCP"""
        addr = writer.get_extra_info('peername')
        print(f"Client connected: {addr}")
        
        try:
            while True:
                data = await reader.read(256)
                if not data:
                    break
                    
                response = self.simulator.process_modbus_frame(data)
                if response:
                    writer.write(response)
                    await writer.drain()
                    
        except Exception as e:
            print(f"Error: {e}")
        finally:
            writer.close()
            await writer.wait_closed()
            
    async def start(self):
        """Uruchom serwer TCP"""
        self.server = await asyncio.start_server(
            self.handle_client, '0.0.0.0', self.port
        )
        print(f"Modbus TCP bridge started on port {self.port}")
        async with self.server:
            await self.server.serve_forever()

# Uruchomienie
if __name__ == '__main__':
    # Uruchom TCP bridge w osobnym wątku
    async def run_tcp_bridge():
        bridge = ModbusTCPBridge(simulator)
        await bridge.start()
        
    def start_bridge():
        asyncio.run(run_tcp_bridge())
        
    bridge_thread = threading.Thread(target=start_bridge)
    bridge_thread.daemon = True
    bridge_thread.start()
    
    # Uruchom Flask API
    app.run(host='0.0.0.0', port=8083)
