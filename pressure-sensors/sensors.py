import asyncio
import struct
import numpy as np
from datetime import datetime


class PressureSensorSimulator:
    """Symulator czujników ciśnienia LP/MP/HP dla C20"""

    def __init__(self):
        self.sensors = {
            0x48: {  # Low Pressure: -60 to +60 mbar
                'name': 'LP',
                'range': (-60, 60),
                'unit': 'mbar',
                'value': 0.0,
                'noise': 0.5
            },
            0x49: {  # Medium Pressure: 0-25 bar
                'name': 'MP',
                'range': (0, 25),
                'unit': 'bar',
                'value': 0.0,
                'noise': 0.1
            },
            0x4A: {  # High Pressure: 0-400 bar
                'name': 'HP',
                'range': (0, 400),
                'unit': 'bar',
                'value': 0.0,
                'noise': 1.0
            }
        }

    async def simulate_pressure_changes(self):
        """Symuluje zmiany ciśnienia w czasie"""
        while True:
            for addr, sensor in self.sensors.items():
                # Symulacja zmian ciśnienia
                if sensor['name'] == 'LP':
                    # Oscylacje wokół zera
                    sensor['value'] = 10 * np.sin(datetime.now().timestamp() / 10)
                elif sensor['name'] == 'MP':
                    # Wolne zmiany
                    sensor['value'] = 12.5 + 5 * np.sin(datetime.now().timestamp() / 30)
                else:  # HP
                    # Stabilne z drobnymi zmianami
                    sensor['value'] = 200 + np.random.normal(0, sensor['noise'])

                # Ogranicz do zakresu
                min_val, max_val = sensor['range']
                sensor['value'] = max(min_val, min(max_val, sensor['value']))

            await asyncio.sleep(0.1)

    def read_sensor(self, address: int) -> bytes:
        """Odczytuje wartość z czujnika"""
        if address in self.sensors:
            sensor = self.sensors[address]
            value = sensor['value']

            # Konwersja na 16-bit (signed dla LP, unsigned dla MP/HP)
            if sensor['name'] == 'LP':
                # Signed 16-bit, rozdzielczość 0.01 mbar
                raw = int(value * 100)
                return struct.pack('>h', raw)  # Big-endian signed short
            else:
                # Unsigned 16-bit, skalowane do pełnego zakresu
                min_val, max_val = sensor['range']
                normalized = (value - min_val) / (max_val - min_val)
                raw = int(normalized * 65535)
                return struct.pack('>H', raw)  # Big-endian unsigned short

        return b'\x00\x00'

    async def handle_i2c_request(self, address: int, register: int) -> bytes:
        """Obsługuje żądania I2C"""
        if register == 0x00:  # Odczyt wartości
            return self.read_sensor(address)
        elif register == 0x01:  # Status czujnika
            return b'\x01' if address in self.sensors else b'\x00'
        elif register == 0x02:  # Kalibracja
            # Symulacja kalibracji
            return b'\xOK'
        else:
            return b'\xFF\xFF'


# Uruchom symulator
async def main():
    simulator = PressureSensorSimulator()

    # Uruchom symulację zmian ciśnienia
    asyncio.create_task(simulator.simulate_pressure_changes())

    # Nasłuchuj na żądania I2C
    # TODO: Implementacja serwera I2C

    while True:
        await asyncio.sleep(1)
        # Debug output
        for addr, sensor in simulator.sensors.items():
            print(f"{sensor['name']}: {sensor['value']:.2f} {sensor['unit']}")


if __name__ == '__main__':
    asyncio.run(main())