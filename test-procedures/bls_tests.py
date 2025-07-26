import asyncio
import json
from dataclasses import dataclass
from typing import Dict, List
from datetime import datetime


@dataclass
class BLSTestResult:
    test_id: str
    device_type: str
    timestamp: datetime
    passed: bool
    measurements: Dict


class BLSTestProcedures:
    """Implementacja procedur testowych dla masek BLS"""

    def __init__(self, hardware_interface):
        self.hw = hardware_interface
        self.current_test = None

    async def test_bls_5000(self, serial_number: str) -> BLSTestResult:
        """Procedura testowa dla maski BLS 5000"""
        test_id = f"BLS5000_{serial_number}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        print(f"Starting test: {test_id}")

        measurements = {}

        try:
            # 1. Zamknij komorę testową
            await self.hw.control_motor('chamber_door', 'close')
            await asyncio.sleep(2)

            # 2. Test szczelności przy ciśnieniu dodatnim
            print("Test 1: Positive pressure leak test")
            await self.hw.set_valve('inlet', True)
            await self.hw.set_pressure('low', 25.0)  # 25 mbar
            await asyncio.sleep(3)  # Stabilizacja

            # Pomiar wycieku
            start_pressure = await self.hw.read_pressure('low')
            await self.hw.set_valve('inlet', False)
            await asyncio.sleep(10)  # 10 sekund testu
            end_pressure = await self.hw.read_pressure('low')

            leak_rate = (start_pressure - end_pressure) / 10
            measurements['leak_rate_positive'] = leak_rate

            # 3. Test zaworu wydechowego
            print("Test 2: Exhalation valve test")
            await self.hw.set_valve('outlet', True)
            await asyncio.sleep(2)
            residual_pressure = await self.hw.read_pressure('low')
            measurements['exhalation_valve_residual'] = residual_pressure

            # 4. Test przy ciśnieniu ujemnym
            print("Test 3: Negative pressure test")
            await self.hw.set_valve('outlet', False)
            await self.hw.set_valve('vacuum', True)
            await self.hw.set_pressure('low', -10.0)  # -10 mbar
            await asyncio.sleep(3)

            measurements['negative_pressure_hold'] = await self.hw.read_pressure('low')

            # 5. Reset
            await self.hw.set_all_valves(False)
            await self.hw.control_motor('chamber_door', 'open')

            # Ocena wyników
            passed = (
                    leak_rate < 0.5 and  # Max 0.5 mbar/s
                    residual_pressure < 2.0 and  # Max 2 mbar
                    measurements['negative_pressure_hold'] < -8.0  # Min -8 mbar
            )

            return BLSTestResult(
                test_id=test_id,
                device_type='BLS_5000',
                timestamp=datetime.now(),
                passed=passed,
                measurements=measurements
            )

        except Exception as e:
            print(f"Test failed with error: {e}")
            return BLSTestResult(
                test_id=test_id,
                device_type='BLS_5000',
                timestamp=datetime.now(),
                passed=False,
                measurements={'error': str(e)}
            )

    async def test_breathing_resistance(self, flow_rate: float = 95.0):
        """Test oporu oddychania przy przepływie 95 L/min"""
        print(f"Testing breathing resistance at {flow_rate} L/min")

        # Ustaw przepływ
        await self.hw.set_flow_rate(flow_rate)
        await asyncio.sleep(2)

        # Zmierz różnicę ciśnień
        pressure_drop = await self.hw.read_pressure('low')

        return {
            'flow_rate': flow_rate,
            'pressure_drop': pressure_drop,
            'resistance': pressure_drop / flow_rate,
            'passed': pressure_drop < 3.0  # Max 3 mbar przy 95 L/min
        }


# Interfejs sprzętowy (mock)
class HardwareInterface:
    """Mock interface dla komunikacji ze sprzętem"""

    async def control_motor(self, motor: str, action: str):
        print(f"Motor {motor}: {action}")
        await asyncio.sleep(0.5)

    async def set_valve(self, valve: str, state: bool):
        print(f"Valve {valve}: {'OPEN' if state else 'CLOSED'}")
        await asyncio.sleep(0.1)

    async def set_all_valves(self, state: bool):
        for valve in ['inlet', 'outlet', 'vacuum', 'purge']:
            await self.set_valve(valve, state)

    async def set_pressure(self, system: str, target: float):
        print(f"Setting {system} pressure to {target}")
        await asyncio.sleep(1)

    async def read_pressure(self, system: str) -> float:
        # Symulowane odczyty
        import random
        if system == 'low':
            return random.uniform(-60, 60)
        elif system == 'medium':
            return random.uniform(0, 25)
        else:  # high
            return random.uniform(0, 400)

    async def set_flow_rate(self, rate: float):
        print(f"Setting flow rate to {rate} L/min")
        await asyncio.sleep(0.5)


# Przykład użycia
async def run_test_example():
    hw = HardwareInterface()
    tester = BLSTestProcedures(hw)

    # Test maski BLS 5000
    result = await tester.test_bls_5000("SN123456")

    print("\n=== TEST RESULTS ===")
    print(f"Test ID: {result.test_id}")
    print(f"Passed: {'YES' if result.passed else 'NO'}")
    print(f"Measurements: {json.dumps(result.measurements, indent=2)}")

    # Test oporu oddychania
    breathing_result = await tester.test_breathing_resistance()
    print(f"\nBreathing resistance: {breathing_result}")


if __name__ == '__main__':
    asyncio.run(run_test_example())