import asyncio
from enum import Enum


class GPIOMode(Enum):
    INPUT = "in"
    OUTPUT = "out"


class GPIOSimulator:
    """Symulator GPIO dla RPi"""

    def __init__(self):
        self.pins = {}
        self.callbacks = {}

    async def setup(self, pin: int, mode: GPIOMode):
        """Konfiguruje pin GPIO"""
        self.pins[pin] = {
            'mode': mode,
            'value': 0,
            'pull': None
        }
        print(f"GPIO: Pin {pin} configured as {mode.value}")

    async def write(self, pin: int, value: int):
        """Ustawia stan pinu"""
        if pin in self.pins and self.pins[pin]['mode'] == GPIOMode.OUTPUT:
            self.pins[pin]['value'] = value
            print(f"GPIO: Pin {pin} = {value}")

            # Wywołaj callbacki jeśli są
            if pin in self.callbacks:
                await self.callbacks[pin](value)
            return True
        return False

    async def read(self, pin: int) -> int:
        """Odczytuje stan pinu"""
        if pin in self.pins:
            return self.pins[pin]['value']
        return 0

    def add_event_detect(self, pin: int, edge: str, callback: Callable):
        """Dodaje detekcję zdarzeń na pinie"""
        self.callbacks[pin] = callback