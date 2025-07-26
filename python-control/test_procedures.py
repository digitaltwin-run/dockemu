#!/usr/bin/env python3
"""
Procedury testowe dla projektu C20 z wykorzystaniem Modbus IO
"""

import asyncio
import time
from modbus_client import ModbusRTUClient

class C20TestProcedures:
    def __init__(self, modbus_client):
        self.client = modbus_client
        self.device_address = 1
        
    async def test_valve_sequence(self):
        """Test sekwencji zaworów dla C20"""
        print("\n=== Test sekwencji zaworów C20 ===")
        
        # Mapowanie zaworów na kanały Modbus IO
        valves = {
            'inlet': 0,      # DO1 - Zawór wlotowy
            'outlet': 1,     # DO2 - Zawór wylotowy
            'purge': 2,      # DO3 - Zawór odpowietrzający
            'test': 3,       # DO4 - Zawór testowy
            'safety1': 4,    # DO5 - Zawór bezpieczeństwa 1
            'safety2': 5,    # DO6 - Zawór bezpieczeństwa 2
            'chamber': 6,    # DO7 - Komora testowa
            'vacuum': 7      # DO8 - Pompa próżniowa
        }
        
        # Sekwencja testowa
        steps = [
            ("Zamknięcie wszystkich zaworów", 'all', 'off'),
            ("Otwarcie zaworu wlotowego", 'inlet', 'on'),
            ("Oczekiwanie na napełnienie", None, 2),
            ("Zamknięcie wlotu, otwarcie testu", 'inlet', 'off'),
            ("", 'test', 'on'),
            ("Test szczelności", None, 5),
            ("Odpowietrzanie", 'test', 'off'),
            ("", 'purge', 'on'),
            ("", None, 2),
            ("Reset systemu", 'all', 'off')
        ]
        
        for step in steps:
            desc, valve, action = step
            if desc:
                print(f"\n{desc}")
            
            if valve == 'all':
                self.client.control_all_outputs(self.device_address, action)
            elif valve is not None:
                valve_channel = valves[valve]
                self.client.control_single_output(
                    self.device_address, 
                    valve_channel, 
                    action
                )
                print(f"  Zawór {valve} (DO{valve_channel+1}): {action}")
            else:
                print(f"  Czekam {action} sekund...")
                await asyncio.sleep(action)
    
    async def test_pressure_monitoring(self):
        """Symulacja monitoringu ciśnienia z użyciem wejść"""
        print("\n=== Test monitoringu ciśnienia ===")
        
        # Mapowanie czujników na wejścia
        sensors = {
            'pressure_low': 0,    # DI1 - Niskie ciśnienie
            'pressure_ok': 1,     # DI2 - Ciśnienie OK
            'pressure_high': 2,   # DI3 - Wysokie ciśnienie
            'leak_detect': 3,     # DI4 - Wykrycie wycieku
            'chamber_closed': 4,  # DI5 - Komora zamknięta
            'emergency': 5,       # DI6 - Przycisk awaryjny
            'ready': 6,          # DI7 - System gotowy
            'alarm': 7           # DI8 - Alarm
        }
        
        # Ustaw tryb Linkage dla alarmów
        print("Konfiguracja trybów kanałów...")
        self.client.set_channel_mode(self.device_address, 3, 1)  # DO4 = DI4 (leak)
        self.client.set_channel_mode(self.device_address, 7, 1)  # DO8 = DI8 (alarm)
        
        # Monitoruj wejścia
        for i in range(10):
            inputs = self.client.read_inputs_status(self.device_address)
            if inputs:
                print(f"\nOdczyt {i+1}:")
                for name, channel in sensors.items():
                    if inputs[channel]:
                        print(f"  ⚠️  {name}: AKTYWNE")
                    
                # Sprawdź stan alarmowy
                if inputs[sensors['emergency']]:
                    print("  🚨 EMERGENCY STOP!")
                    self.client.control_all_outputs(self.device_address, 'off')
                    break
                    
            await asyncio.sleep(1)
    
    async def test_bls_mask_procedure(self):
        """Procedura testowa maski BLS"""
        print("\n=== Procedura testowa maski BLS ===")
        
        # Konfiguracja
        test_pressure_channel = 0  # DO1 - Ciśnienie testowe
        vacuum_channel = 7         # DO8 - Pompa próżniowa
        
        # Miganie LED podczas testu
        self.client.flash_output(self.device_address, 6, 5, 5)  # DO7 - miga co 500ms
        
        print("1. Inicjalizacja testu...")
        self.client.control_all_outputs(self.device_address, 'off')
        await asyncio.sleep(1)
        
        print("2. Test ciśnienia dodatniego...")
        self.client.control_single_output(self.device_address, test_pressure_channel, 'on')
        await asyncio.sleep(3)
        
        # Odczyt wyniku (symulacja)
        outputs = self.client.read_outputs_status(self.device_address)
        if outputs and outputs[test_pressure_channel]:
            print("   ✓ Ciśnienie utrzymane")
        else:
            print("   ✗ Wykryto wyciek")
        
        print("3. Test podciśnienia...")
        self.client.control_single_output(self.device_address, test_pressure_channel, 'off')
        self.client.control_single_output(self.device_address, vacuum_channel, 'on')
        await asyncio.sleep(3)
        
        print("4. Zakończenie testu...")
        self.client.control_all_outputs(self.device_address, 'off')
        
        # Zatrzymaj miganie
        self.client.flash_output(self.device_address, 6, 0)

async def main():
    """Główna funkcja testowa"""
    # Połącz z symulatorem
    client = ModbusRTUClient(tcp_host='localhost', tcp_port=5020)
    tester = C20TestProcedures(client)
    
    try:
        # Uruchom testy
        await tester.test_valve_sequence()
        await tester.test_pressure_monitoring()
        await tester.test_bls_mask_procedure()
        
    finally:
        client.close()

if __name__ == '__main__':
    asyncio.run(main())
