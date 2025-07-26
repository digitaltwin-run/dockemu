from pymodbus.server import StartTcpServer
from pymodbus.datastore import ModbusSequentialDataBlock, ModbusSlaveContext, ModbusServerContext
from pymodbus.transaction import ModbusRtuFramer, ModbusAsciiFramer
import threading
import time

class ModbusSimulator:
    def __init__(self, host='0.0.0.0', port=502):
        self.host = host
        self.port = port
        self.store = {
            'h': ModbusSequentialDataBlock(0, [0] * 100),  # Holding registers
            'c': ModbusSequentialDataBlock(0, [0] * 100),  # Coils
            'i': ModbusSequentialDataBlock(0, [0] * 100),  # Input registers
            'd': ModbusSequentialDataBlock(0, [0] * 100)   # Discrete inputs
        }
        self.context = ModbusSlaveContext(
            hr=self.store['h'],  # Holding registers
            ir=self.store['i'],  # Input registers
            co=self.store['c'],  # Coils
            di=self.store['d']   # Discrete inputs
        )
        self.server_context = ModbusServerContext(slaves=self.context, single=True)

    def start(self):
        print(f"Starting Modbus TCP Server on {self.host}:{self.port}")
        self.server = StartTcpServer(
            context=self.server_context,
            address=(self.host, self.port),
            framer=ModbusRtuFramer
        )

    def update_register(self, register_type, address, value):
        """Update a specific register value"""
        if register_type in self.store:
            self.store[register_type].setValues(0, [address], [value])
            return True
        return False

def run_modbus_simulator():
    simulator = ModbusSimulator()
    server_thread = threading.Thread(target=simulator.start)
    server_thread.daemon = True
    server_thread.start()
    
    try:
        while True:
            # Example: Toggle some values periodically
            current_value = simulator.store['h'].getValues(0, 0, 1)[0]
            simulator.update_register('h', 0, 1 - current_value)
            time.sleep(5)
    except KeyboardInterrupt:
        print("Shutting down Modbus simulator...")

if __name__ == "__main__":
    run_modbus_simulator()
