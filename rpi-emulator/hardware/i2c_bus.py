class I2CBus:
    """
    I2C Bus emulator for Raspberry Pi
    """
    def __init__(self, bus_number=1):
        self.bus_number = bus_number
        self.devices = {}

    def write_byte_data(self, address, register, value):
        if address not in self.devices:
            self.devices[address] = {}
        self.devices[address][register] = value
        print(f"I2C write - Address: 0x{address:02X}, Register: 0x{register:02X}, Value: 0x{value:02X}")

    def read_byte_data(self, address, register):
        if address in self.devices and register in self.devices[address]:
            return self.devices[address][register]
        return 0xFF

    def close(self):
        self.devices.clear()
