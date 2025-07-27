# Hardware Simulation & Standardized Port Connection Research

## Analiza Obecnych Problemów w Symulacji Sprzętowej

### Problemy z Obecnym Podejściem
1. **QEMU** - ciężki, nadmiarowy dla prostej diagnostyki
2. **Rozproszenie technologii** - brak ujednoliconego interfejsu
3. **Brak standaryzacji portów** - każdy serwis ma własne połączenia
4. **Trudna diagnostyka** - złożone zależności między serwisami

## Rekomendowane Rozwiązania dla Symulacji Sprzętowej

### 1. **SimulationCore - Uniwersalny Framework**

```python
# simulation-core/core_framework.py
import asyncio
import json
from typing import Dict, Any, List
from abc import ABC, abstractmethod

class HardwareInterface(ABC):
    """Abstract interface for all hardware types"""
    
    @abstractmethod
    async def initialize(self) -> bool:
        pass
    
    @abstractmethod
    async def send_data(self, data: bytes) -> bytes:
        pass
    
    @abstractmethod
    async def get_status(self) -> Dict[str, Any]:
        pass

class I2CInterface(HardwareInterface):
    """I2C Bus simulation"""
    
    def __init__(self, bus_id: int = 1):
        self.bus_id = bus_id
        self.devices = {}  # address -> device_simulation
        self.is_active = False
    
    async def initialize(self) -> bool:
        """Initialize I2C bus"""
        self.is_active = True
        return True
    
    async def scan_devices(self) -> List[int]:
        """Scan for I2C devices on bus"""
        active_devices = []
        for addr in range(0x08, 0x78):  # Valid I2C address range
            if addr in self.devices:
                active_devices.append(addr)
        return active_devices
    
    async def send_data(self, address: int, data: bytes) -> bytes:
        """Send data to I2C device"""
        if address in self.devices:
            device = self.devices[address]
            return await device.process_data(data)
        return b'\x00'  # No device response
    
    async def get_status(self) -> Dict[str, Any]:
        return {
            'bus_id': self.bus_id,
            'active': self.is_active,
            'device_count': len(self.devices),
            'devices': list(self.devices.keys())
        }
    
    def add_device(self, address: int, device_simulator):
        """Add simulated device to bus"""
        self.devices[address] = device_simulator

class RS232Interface(HardwareInterface):
    """RS232/Serial Port simulation"""
    
    def __init__(self, port: str, baudrate: int = 9600):
        self.port = port
        self.baudrate = baudrate
        self.is_connected = False
        self.buffer = bytearray()
    
    async def initialize(self) -> bool:
        self.is_connected = True
        return True
    
    async def send_data(self, data: bytes) -> bytes:
        # Simulate echo or device response
        if self.is_connected:
            # Simple echo simulation
            return data
        return b''
    
    async def get_status(self) -> Dict[str, Any]:
        return {
            'port': self.port,
            'baudrate': self.baudrate,
            'connected': self.is_connected,
            'buffer_size': len(self.buffer)
        }

class USBInterface(HardwareInterface):
    """USB Device simulation"""
    
    def __init__(self, vendor_id: int, product_id: int):
        self.vendor_id = vendor_id
        self.product_id = product_id
        self.is_enumerated = False
        self.device_class = 'HID'  # Human Interface Device
    
    async def initialize(self) -> bool:
        self.is_enumerated = True
        return True
    
    async def send_data(self, data: bytes) -> bytes:
        # USB HID simulation
        return data[:64]  # HID report size limit
    
    async def get_status(self) -> Dict[str, Any]:
        return {
            'vendor_id': f'0x{self.vendor_id:04x}',
            'product_id': f'0x{self.product_id:04x}',
            'enumerated': self.is_enumerated,
            'class': self.device_class
        }

class HDMIInterface(HardwareInterface):
    """HDMI/DVI Video Output simulation"""
    
    def __init__(self, resolution: tuple = (1920, 1080)):
        self.resolution = resolution
        self.refresh_rate = 60
        self.is_connected = False
        self.signal_type = 'HDMI'
    
    async def initialize(self) -> bool:
        self.is_connected = True
        return True
    
    async def send_data(self, frame_data: bytes) -> bytes:
        # Video frame processing simulation
        return b'ACK'  # Acknowledge frame received
    
    async def get_status(self) -> Dict[str, Any]:
        return {
            'resolution': f'{self.resolution[0]}x{self.resolution[1]}',
            'refresh_rate': f'{self.refresh_rate}Hz',
            'connected': self.is_connected,
            'signal_type': self.signal_type
        }

class UnifiedHardwareSimulator:
    """Central hub for all hardware simulations"""
    
    def __init__(self):
        self.interfaces = {}
        self.is_running = False
    
    def register_interface(self, name: str, interface: HardwareInterface):
        """Register hardware interface"""
        self.interfaces[name] = interface
    
    async def initialize_all(self):
        """Initialize all registered interfaces"""
        results = {}
        for name, interface in self.interfaces.items():
            results[name] = await interface.initialize()
        self.is_running = True
        return results
    
    async def get_system_status(self):
        """Get status of all hardware interfaces"""
        status = {'system_running': self.is_running, 'interfaces': {}}
        
        for name, interface in self.interfaces.items():
            status['interfaces'][name] = await interface.get_status()
        
        return status
    
    async def scan_hardware(self):
        """Scan and detect all hardware"""
        detected = {}
        
        for name, interface in self.interfaces.items():
            if isinstance(interface, I2CInterface):
                detected[name] = {
                    'type': 'I2C',
                    'devices': await interface.scan_devices()
                }
            else:
                detected[name] = {
                    'type': interface.__class__.__name__,
                    'status': await interface.get_status()
                }
        
        return detected
```

### 2. **Standardized Device Simulators**

```python
# simulation-core/device_simulators.py
class RPiGPIODevice:
    """Simulate Raspberry Pi GPIO pins"""
    
    def __init__(self):
        self.pins = {i: {'mode': 'input', 'value': 0} for i in range(1, 41)}
        self.i2c_enabled = False
        self.spi_enabled = False
    
    async def process_data(self, data: bytes) -> bytes:
        # GPIO command simulation
        if data.startswith(b'GPIO_SET'):
            # Parse GPIO set command
            pin, value = self.parse_gpio_command(data)
            self.pins[pin]['value'] = value
            return b'OK'
        elif data.startswith(b'GPIO_GET'):
            pin = self.parse_gpio_command(data)[0]
            return str(self.pins[pin]['value']).encode()
        return b'ERROR'
    
    def parse_gpio_command(self, data: bytes):
        # Simple command parsing
        parts = data.decode().split('_')
        return int(parts[2]), int(parts[3]) if len(parts) > 3 else None

class TemperatureSensor:
    """Simulate temperature sensor (e.g., DS18B20)"""
    
    def __init__(self, base_temp: float = 25.0):
        self.base_temp = base_temp
        self.variation = 2.0
    
    async def process_data(self, data: bytes) -> bytes:
        import random
        # Simulate temperature reading with variation
        current_temp = self.base_temp + random.uniform(-self.variation, self.variation)
        return f'{current_temp:.2f}'.encode()

class PressureSensor:
    """Simulate pressure sensor"""
    
    def __init__(self, base_pressure: float = 101325.0):
        self.base_pressure = base_pressure  # Pa
    
    async def process_data(self, data: bytes) -> bytes:
        import random
        pressure = self.base_pressure + random.uniform(-1000, 1000)
        return f'{pressure:.0f}'.encode()
```

### 3. **Web-based Hardware Monitor**

```php
<?php
// hardware-monitor/monitor.php
class HardwareMonitor {
    private $simulator_api;
    
    public function __construct() {
        $this->simulator_api = 'http://localhost:8061/api/';
    }
    
    public function getHardwareStatus() {
        $status = @file_get_contents($this->simulator_api . 'status');
        return $status ? json_decode($status, true) : [];
    }
    
    public function renderHardwareDashboard() {
        $status = $this->getHardwareStatus();
        ?>
        <div class="hardware-dashboard">
            <h2>🔧 Hardware Simulation Dashboard</h2>
            
            <div class="interface-grid">
                <?php foreach ($status['interfaces'] ?? [] as $name => $interface): ?>
                    <div class="interface-card">
                        <h4><?php echo strtoupper($name); ?></h4>
                        <div class="interface-details">
                            <?php foreach ($interface as $key => $value): ?>
                                <div class="detail-row">
                                    <span class="key"><?php echo $key; ?>:</span>
                                    <span class="value"><?php echo is_array($value) ? json_encode($value) : $value; ?></span>
                                </div>
                            <?php endforeach; ?>
                        </div>
                    </div>
                <?php endforeach; ?>
            </div>
            
            <div class="control-panel">
                <h3>Hardware Control</h3>
                <button onclick="scanHardware()">🔍 Scan Hardware</button>
                <button onclick="resetSimulation()">🔄 Reset Simulation</button>
                <button onclick="exportConfiguration()">💾 Export Config</button>
            </div>
        </div>
        
        <script>
        function scanHardware() {
            fetch('<?php echo $this->simulator_api; ?>scan')
                .then(response => response.json())
                .then(data => {
                    console.log('Hardware scan result:', data);
                    location.reload();
                });
        }
        
        function resetSimulation() {
            fetch('<?php echo $this->simulator_api; ?>reset', {method: 'POST'})
                .then(response => response.json())
                .then(data => {
                    console.log('Reset result:', data);
                    location.reload();
                });
        }
        </script>
        <?php
    }
}
?>
```

## Najlepsze Narzędzia do Symulacji Hardware

### 1. **Renode** - Profesjonalny Framework
- **Zalety**: Pełna symulacja embedded systems, ARM, RISC-V
- **Użycie**: `renode --console --script rpi3.resc`
- **Integracja**: REST API, WebSocket połączenia

### 2. **QEMU z Uproszczonym Interfejsem**
```bash
# Simplified QEMU wrapper
#!/bin/bash
# simple-qemu.sh
qemu-system-aarch64 \
    -M raspi3b \
    -cpu cortex-a72 \
    -m 1G \
    -netdev user,id=net0,hostfwd=tcp::2222-:22 \
    -device usb-net,netdev=net0 \
    -vnc :1 \
    -monitor telnet:127.0.0.1:4444,server,nowait \
    -serial stdio
```

### 3. **Docker-based Hardware Abstraction**
```dockerfile
# Dockerfile.hardware-sim
FROM python:3.11-alpine

RUN apk add --no-cache \
    socat \
    minicom \
    i2c-tools

# Install Python simulation libraries
RUN pip install \
    pyserial \
    smbus2 \
    RPi.GPIO \
    flask \
    websockets

COPY simulation-core/ /app/
WORKDIR /app

# Expose standard ports
EXPOSE 8061 2222 5901

CMD ["python", "hardware_simulator.py"]
```

## Standaryzacja Portów - Rekomendacje

### Port Schema (w .env)
```bash
# === STANDARDIZED HARDWARE PORTS ===
# Base Hardware Simulation
HARDWARE_BRIDGE_PORT=8061
HARDWARE_API_PORT=8062

# Standard Interface Ports
I2C_SIMULATOR_PORT=8071
RS232_SIMULATOR_PORT=8072  
USB_SIMULATOR_PORT=8073
HDMI_SIMULATOR_PORT=8074
GPIO_SIMULATOR_PORT=8075

# Device-specific Ports  
TEMP_SENSORS_PORT=8081
PRESSURE_SENSORS_PORT=8082
VALVE_CONTROLLER_PORT=8083
LCD_DISPLAY_PORT=8084

# Communication Protocols
MQTT_PORT=1883
MODBUS_TCP_PORT=502
OPC_UA_PORT=4840
```

### Unified Configuration System
```php
<?php
// config/hardware_config.php
class HardwareConfig {
    private $interfaces = [
        'i2c' => [
            'port' => 8071,
            'devices' => [
                '0x20' => 'GPIO_Expander',
                '0x48' => 'Temperature_Sensor',
                '0x77' => 'Pressure_Sensor'
            ]
        ],
        'rs232' => [
            'port' => 8072,
            'baudrates' => [9600, 19200, 38400, 115200],
            'devices' => ['ttyUSB0', 'ttyAMA0']
        ],
        'usb' => [
            'port' => 8073,
            'devices' => [
                ['vid' => '0x1234', 'pid' => '0x5678', 'class' => 'HID'],
                ['vid' => '0x0483', 'pid' => '0x5740', 'class' => 'CDC']
            ]
        ]
    ];
    
    public function generateDockerCompose() {
        $services = [];
        
        foreach ($this->interfaces as $name => $config) {
            $services[$name . '-sim'] = [
                'build' => './hardware-sim',
                'ports' => ["{$config['port']}:80"],
                'environment' => [
                    'INTERFACE_TYPE' => strtoupper($name),
                    'CONFIG' => json_encode($config)
                ]
            ];
        }
        
        return yaml_emit(['services' => $services]);
    }
}
?>
```

## Implementacja - Przykład Uruchomienia

### 1. Utworzenie Uproszczonego docker-compose.yml
```yaml
version: '3.8'

services:
  # === SIMPLIFIED CORE SERVICES ===
  dashboard:
    build: ./dashboard
    ports: ["8060:80"]
    volumes: [".env:/var/www/html/.env"]
    
  hardware-sim:
    build: ./hardware-sim  
    ports: 
      - "8061:80"      # Web interface
      - "8071:8071"    # I2C
      - "8072:8072"    # RS232
      - "8073:8073"    # USB
    privileged: true
    devices:
      - "/dev/i2c-1:/dev/i2c-1"
      - "/dev/ttyUSB0:/dev/ttyUSB0"
    
  rpi-simple:
    image: balenalib/raspberry-pi-alpine-python
    ports: ["2222:22", "5901:5901"]
    volumes: ["./shared:/shared"]
    
  mqtt:
    image: eclipse-mosquitto:2.0
    ports: ["1883:1883"]
```

### 2. Narzędzie Diagnostyczne
```bash
#!/bin/bash
# tools/unified-diagnostic.sh

echo "=== C20 Unified Hardware Diagnostic ==="
echo

echo "1. System Status:"
docker-compose ps --format "table {{.Service}}\t{{.State}}\t{{.Ports}}"
echo

echo "2. Hardware Interfaces:"
curl -s http://localhost:8061/api/scan | jq '.'
echo

echo "3. Port Connectivity:"
for port in 8060 8061 2222 5901 1883; do
    if nc -z localhost $port 2>/dev/null; then
        echo "✅ Port $port: OPEN"
    else
        echo "❌ Port $port: CLOSED"
    fi
done
echo

echo "4. Environment Variables:"
grep -E '_PORT=' .env | sort
echo

echo "5. Hardware Test:"
python3 << EOF
import requests
try:
    response = requests.get('http://localhost:8061/api/test')
    print(f"Hardware API: {response.status_code} - {response.text}")
except:
    print("❌ Hardware API not responding")
EOF
```

## Korzyści z Nowego Podejścia

1. **🎯 Jednolity interfejs** - wszystkie porty przez jeden API
2. **🔧 Łatwa diagnostyka** - jeden dashboard dla całego hardware  
3. **⚡ Szybkie uruchamianie** - 4 serwisy zamiast 25+
4. **🔗 Standaryzacja** - wszystkie porty w jednym miejscu
5. **🐛 Lepsze debugowanie** - scentralizowane logi i monitoring
6. **📱 Responsive UI** - nowoczesny interfejs PHP + JavaScript

## Następne Kroki

1. Implementacja `hardware-sim` kontenera
2. Integracja z uproszczonym `dashboard`  
3. Migracja istniejących serwisów do nowego API
4. Testowanie i optymalizacja

Czy chcesz żebym rozpoczął implementację któregoś z tych komponentów?