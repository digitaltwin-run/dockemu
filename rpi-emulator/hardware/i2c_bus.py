import asyncio
import json
from typing import Dict, List, Callable


class I2CBusSimulator:
    """Symulator magistrali I2C dla projektu C20"""

    def __init__(self):
        self.devices: Dict[int, 'I2CDevice'] = {}
        self.bus_lock = asyncio.Lock()

    async def register_device(self, address: int, device: 'I2CDevice'):
        """Rejestruje urządzenie na magistrali I2C"""
        async with self.bus_lock:
            self.devices[address] = device
            print(f"I2C: Registered device at 0x{address:02X}")

    async def write(self, address: int, data: bytes) -> bool:
        """Wysyła dane do urządzenia I2C"""
        async with self.bus_lock:
            if address in self.devices:
                return await self.devices[address].write(data)
            return False

    async def read(self, address: int, length: int) -> bytes:
        """Odczytuje dane z urządzenia I2C"""
        async with self.bus_lock:
            if address in self.devices:
                return await self.devices[address].read(length)
            return b'\xFF' * length


class I2CDevice:
    """Bazowa klasa dla urządzeń I2C"""

    def __init__(self, address: int, name: str):
        self.address = address
        self.name = name
        self.registers = {}

    async def write(self, data: bytes) -> bool:
        """Obsługa zapisu do urządzenia"""
        if len(data) >= 2:
            register = data[0]
            value = data[1:]
            self.registers[register] = value
            return True
        return False

    async def read(self, length: int) -> bytes:
        """Obsługa odczytu z urządzenia"""
        # Domyślna implementacja
        return bytes([0x00] * length)


# Przykład: Symulator PCB Keyboard
class PCBKeyboardSimulator(I2CDevice):
    def __init__(self):
        super().__init__(0x20, "PCB Keyboard HUI")
        self.key_states = [False] * 11  # 9+2 przyciski
        self.encoder_position = 0

    async def read(self, length: int) -> bytes:
        """Zwraca stan przycisków i enkodera"""
        if length >= 2:
            # Bajt 1: stan przycisków (bity 0-10)
            key_byte = sum(1 << i for i, state in enumerate(self.key_states) if state)
            # Bajt 2: pozycja enkodera
            return bytes([key_byte & 0xFF, (key_byte >> 8) & 0xFF, self.encoder_position])
        return b'\x00' * length