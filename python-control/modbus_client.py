#!/usr/bin/env python3
"""
Klient Modbus RTU do sterowania modułem IO 8CH
Zgodny z przykładami z dokumentacji Waveshare
"""

import serial
import struct
import time
import socket

class ModbusRTUClient:
    def __init__(self, port=None, tcp_host=None, tcp_port=5020):
        """
        Inicjalizacja klienta Modbus RTU
        port: port szeregowy (np. '/dev/ttyUSB0')
        tcp_host: host TCP (dla trybu bridge)
        tcp_port: port TCP
        """
        self.tcp_mode = tcp_host is not None
        
        if self.tcp_mode:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.connect((tcp_host, tcp_port))
            print(f"Connected to TCP bridge at {tcp_host}:{tcp_port}")
        else:
            self.ser = serial.Serial(
                port=port,
                baudrate=9600,
                bytesize=8,
                parity='N',
                stopbits=1,
                timeout=1
            )
            print(f"Connected to serial port {port}")
    
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
    
    def send_command(self, command):
        """Wyślij komendę i odbierz odpowiedź"""
        # Dodaj CRC jeśli nie ma
        if len(command) >= 3:
            crc = self.calculate_crc16(command)
            command_with_crc = command + crc
        else:
            command_with_crc = command
            
        print(f"TX: {command_with_crc.hex().upper()}")
        
        if self.tcp_mode:
            self.sock.send(command_with_crc)
            response = self.sock.recv(256)
        else:
            self.ser.write(command_with_crc)
            time.sleep(0.05)
            response = self.ser.read(256)
            
        if response:
            print(f"RX: {response.hex().upper()}")
            return response
        return None
    
    def control_single_output(self, address, channel, action):
        """
        Kontrola pojedynczego wyjścia
        address: adres urządzenia (1-255)
        channel: numer kanału (0-7)
        action: 'on', 'off', 'toggle'
        """
        actions = {
            'on': 0xFF00,
            'off': 0x0000,
            'toggle': 0x5500
        }
        
        command = struct.pack('>BBHH', address, 0x05, channel, actions[action])
        return self.send_command(command)
    
    def control_all_outputs(self, address, action):
        """Kontrola wszystkich wyjść"""
        actions = {
            'on': 0xFF00,
            'off': 0x0000,
            'toggle': 0x5500
        }
        
        command = struct.pack('>BBHH', address, 0x05, 0x00FF, actions[action])
        return self.send_command(command)
    
    def read_outputs_status(self, address):
        """Odczyt stanu wyjść"""
        command = struct.pack('>BBHH', address, 0x01, 0x0000, 0x0008)
        response = self.send_command(command)
        
        if response and len(response) >= 6:
            status_byte = response[3]
            outputs = []
            for i in range(8):
                outputs.append(bool(status_byte & (1 << i)))
            return outputs
        return None
    
    def read_inputs_status(self, address):
        """Odczyt stanu wejść"""
        command = struct.pack('>BBHH', address, 0x02, 0x0000, 0x0008)
        response = self.send_command(command)
        
        if response and len(response) >= 6:
            status_byte = response[3]
            inputs = []
            for i in range(8):
                inputs.append(bool(status_byte & (1 << i)))
            return inputs
        return None
    
    def set_channel_mode(self, address, channel, mode):
        """
        Ustaw tryb kanału
        mode: 0=Normal, 1=Linkage, 2=Toggle, 3=Edge Trigger
        """
        register = 0x1000 + channel
        command = struct.pack('>BBHH', address, 0x06, register, mode)
        return self.send_command(command)
    
    def flash_output(self, address, channel, on_time, off_time=None):
        """
        Ustaw miganie wyjścia
        on_time: czas włączenia (x100ms)
        off_time: czas wyłączenia (x100ms)
        """
        # Flash ON
        register = 0x0200 + channel
        command = struct.pack('>BBHH', address, 0x05, register, on_time)
        self.send_command(command)
        
        # Flash OFF
        if off_time is not None:
            register = 0x0400 + channel
            command = struct.pack('>BBHH', address, 0x05, register, off_time)
            self.send_command(command)
    
    def close(self):
        """Zamknij połączenie"""
        if self.tcp_mode:
            self.sock.close()
        else:
            self.ser.close()

# Przykłady użycia zgodne z dokumentacją
def example_basic_control():
    """Przykład podstawowej kontroli"""
    print("=== Przykład podstawowej kontroli ===")
    
    # Połącz przez TCP bridge (dla symulacji)
    client = ModbusRTUClient(tcp_host='localhost', tcp_port=5020)
    
    try:
        # Przykłady z dokumentacji
        print("\n1. Włączanie pojedynczych wyjść:")
        client.control_single_output(1, 0, 'on')   # 01 05 00 00 FF 00 8C 3A
        time.sleep(0.5)
        client.control_single_output(1, 1, 'on')   # 01 05 00 01 FF 00 DD FA
        time.sleep(0.5)
        
        print("\n2. Wyłączanie wyjść:")
        client.control_single_output(1, 0, 'off')  # 01 05 00 00 00 00 CD CA
        time.sleep(0.5)
        client.control_single_output(1, 1, 'off')  # 01 05 00 01 00 00 9C 0A
        time.sleep(0.5)
        
        print("\n3. Toggle wyjść:")
        client.control_single_output(1, 0, 'toggle')  # 01 05 00 00 55 00 F2 9A
        time.sleep(0.5)
        client.control_single_output(1, 1, 'toggle')  # 01 05 00 01 55 00 A3 5A
        
        print("\n4. Kontrola wszystkich wyjść:")
        client.control_all_outputs(1, 'on')    # 01 05 00 FF FF 00 BC 0A
        time.sleep(1)
        client.control_all_outputs(1, 'off')   # 01 05 00 FF 00 00 FD FA
        time.sleep(1)
        client.control_all_outputs(1, 'toggle') # 01 05 00 FF 55 00 C2 AA
        
    finally:
        client.close()

def example_advanced_features():
    """Przykład zaawansowanych funkcji"""
    print("\n=== Przykład zaawansowanych funkcji ===")
    
    client = ModbusRTUClient(tcp_host='localhost', tcp_port=5020)
    
    try:
        print("\n1. Odczyt stanu wyjść:")
        outputs = client.read_outputs_status(1)
        if outputs:
            for i, state in enumerate(outputs):
                print(f"   DO{i+1}: {'ON' if state else 'OFF'}")
        
        print("\n2. Odczyt stanu wejść:")
        inputs = client.read_inputs_status(1)
        if inputs:
            for i, state in enumerate(inputs):
                print(f"   DI{i+1}: {'ON' if state else 'OFF'}")
        
        print("\n3. Ustawianie trybów kanałów:")
        client.set_channel_mode(1, 0, 1)  # Kanał 1 - Linkage mode
        time.sleep(0.5)
        client.set_channel_mode(1, 1, 2)  # Kanał 2 - Toggle mode
        
        print("\n4. Miganie wyjść:")
        client.flash_output(1, 0, 7)      # Kanał 1 - flash ON 700ms
        client.flash_output(1, 1, 8, 6)   # Kanał 2 - ON 800ms, OFF 600ms
        
    finally:
        client.close()

def example_test_sequence():
    """Przykład sekwencji testowej"""
    print("\n=== Przykład sekwencji testowej ===")
    
    client = ModbusRTUClient(tcp_host='localhost', tcp_port=5020)
    
    try:
        print("\n1. Test sekwencyjny wyjść:")
        for i in range(8):
            print(f"   Włączam DO{i+1}")
            client.control_single_output(1, i, 'on')
            time.sleep(0.3)
        
        time.sleep(1)
        
        for i in range(8):
            print(f"   Wyłączam DO{i+1}")
            client.control_single_output(1, i, 'off')
            time.sleep(0.3)
        
        print("\n2. Test wzorców:")
        patterns = [
            (0x55, "01010101"),  # Co drugi
            (0xAA, "10101010"),  # Odwrotnie
            (0x0F, "00001111"),  # Połowa
            (0xF0, "11110000"),  # Druga połowa
        ]
        
        for pattern, desc in patterns:
            print(f"   Wzór: {desc}")
            # Użyj Write Multiple Coils (0x0F)
            command = struct.pack('>BBHHBB', 
                1,      # Address
                0x0F,   # Function
                0x0000, # Start address
                0x0008, # Count
                0x01,   # Byte count
                pattern # Pattern
            )
            client.send_command(command)
            time.sleep(1)
        
    finally:
        client.close()

if __name__ == '__main__':
    # Uruchom przykłady
    example_basic_control()
    example_advanced_features()
    example_test_sequence()
