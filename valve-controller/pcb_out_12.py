import asyncio
import struct
from typing import List, Dict


class PCBOut12Simulator:
    """Symulator PCB OUT 12 - 12 wyjść 24V/0.5A"""

    def __init__(self, i2c_address: int = 0x21):
        self.address = i2c_address
        self.outputs = [False] * 12  # Stan 12 wyjść
        self.current_draw = [0.0] * 12  # Pobór prądu
        self.fuses = [True] * 12  # Stan bezpieczników
        self.temperature = 25.0  # Temperatura PCB

        # Rejestry I2C
        self.registers = {
            0x00: self._read_outputs,  # Stan wyjść (2 bajty)
            0x02: self._read_current,  # Pobór prądu
            0x04: self._read_fuses,  # Stan bezpieczników
            0x06: self._read_temperature,  # Temperatura
            0x10: self._write_output,  # Kontrola pojedynczego wyjścia
            0x20: self._write_all_outputs,  # Kontrola wszystkich wyjść
            0x30: self._reset_fuse  # Reset bezpiecznika
        }

    def _read_outputs(self) -> bytes:
        """Zwraca stan wszystkich wyjść jako 2 bajty"""
        state = 0
        for i, output in enumerate(self.outputs):
            if output:
                state |= (1 << i)
        return struct.pack('>H', state)

    def _read_current(self) -> bytes:
        """Zwraca pobór prądu (symulowany)"""
        # Średni pobór prądu
        avg_current = sum(self.current_draw) / len(self.current_draw)
        return struct.pack('>H', int(avg_current * 1000))  # mA

    def _read_fuses(self) -> bytes:
        """Zwraca stan bezpieczników"""
        state = 0
        for i, fuse_ok in enumerate(self.fuses):
            if fuse_ok:
                state |= (1 << i)
        return struct.pack('>H', state)

    def _read_temperature(self) -> bytes:
        """Zwraca temperaturę PCB"""
        return struct.pack('>h', int(self.temperature * 10))  # 0.1°C

    def _write_output(self, channel: int, state: bool):
        """Kontroluje pojedyncze wyjście"""
        if 0 <= channel < 12:
            if not self.fuses[channel]:
                print(f"Output {channel} - blown fuse!")
                return False

            self.outputs[channel] = state

            # Symuluj pobór prądu
            if state:
                self.current_draw[channel] = 0.3 + (channel * 0.02)  # 300-320mA
            else:
                self.current_draw[channel] = 0.0

            print(f"Output {channel} = {'ON' if state else 'OFF'}")

            # Symuluj wzrost temperatury
            active_outputs = sum(self.outputs)
            self.temperature = 25.0 + (active_outputs * 2.5)

            # Sprawdź przeciążenie
            if self.current_draw[channel] > 0.5:  # 500mA limit
                self.fuses[channel] = False
                self.outputs[channel] = False
                print(f"Output {channel} - overcurrent protection triggered!")

            return True
        return False

    def _write_all_outputs(self, state: int):
        """Ustawia wszystkie wyjścia jednocześnie"""
        for i in range(12):
            self._write_output(i, bool(state & (1 << i)))

    def _reset_fuse(self, channel: int):
        """Reset bezpiecznika"""
        if 0 <= channel < 12:
            self.fuses[channel] = True
            self.current_draw[channel] = 0.0
            print(f"Fuse {channel} reset")

    async def process_i2c_command(self, register: int, data: bytes = None) -> bytes:
        """Przetwarza komendę I2C"""
        if register in self.registers:
            handler = self.registers[register]

            if data is None:  # Odczyt
                return handler()
            else:  # Zapis
                if register == 0x10:  # Pojedyncze wyjście
                    channel = data[0]
                    state = bool(data[1])
                    handler(channel, state)
                elif register == 0x20:  # Wszystkie wyjścia
                    state = struct.unpack('>H', data)[0]
                    handler(state)
                elif register == 0x30:  # Reset bezpiecznika
                    channel = data[0]
                    handler(channel)

        return b'\x00\x00'

    async def run_diagnostics(self):
        """Okresowa diagnostyka"""
        while True:
            await asyncio.sleep(5)

            # Sprawdź temperaturę
            if self.temperature > 60:
                print(f"WARNING: High temperature: {self.temperature}°C")

            # Sprawdź bezpieczniki
            blown_fuses = [i for i, fuse in enumerate(self.fuses) if not fuse]
            if blown_fuses:
                print(f"Blown fuses: {blown_fuses}")


# Przykład użycia z procedurą testową
class ValveTestProcedure:
    def __init__(self, pcb: PCBOut12Simulator):
        self.pcb = pcb

    async def test_sequence(self):
        """Przykładowa sekwencja testowa zaworów"""
        print("Starting valve test sequence...")

        # Test 1: Pojedyncze zawory
        for i in range(12):
            await self.pcb.process_i2c_command(0x10, bytes([i, 1]))
            await asyncio.sleep(0.5)
            await self.pcb.process_i2c_command(0x10, bytes([i, 0]))
            await asyncio.sleep(0.2)

        # Test 2: Wszystkie zawory
        print("All valves ON")
        await self.pcb.process_i2c_command(0x20, struct.pack('>H', 0xFFF))
        await asyncio.sleep(2)

        print("All valves OFF")
        await self.pcb.process_i2c_command(0x20, struct.pack('>H', 0x000))

        # Test 3: Wzór
        patterns = [0x555, 0xAAA, 0xF0F, 0x0F0]
        for pattern in patterns:
            print(f"Pattern: {pattern:03X}")
            await self.pcb.process_i2c_command(0x20, struct.pack('>H', pattern))
            await asyncio.sleep(1)

        print("Test sequence completed")


async def main():
    pcb = PCBOut12Simulator()
    tester = ValveTestProcedure(pcb)

    # Uruchom diagnostykę w tle
    asyncio.create_task(pcb.run_diagnostics())

    # Uruchom sekwencję testową
    await tester.test_sequence()


if __name__ == '__main__':
    asyncio.run(main())