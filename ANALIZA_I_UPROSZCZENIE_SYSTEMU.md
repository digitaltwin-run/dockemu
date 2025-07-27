# Analiza i Uproszczenie Systemu C20 - Rozwiązanie Problemów Diagnostycznych

## Obecne Problemy Zidentyfikowane

### 1. **BRAK DOSTĘPU DO RPI3 W HMI-MONITOR**
- HMI Monitor nie pokazuje procesu ładowania RPI3
- Brak integracji z rpi-qemu i rpi3pc w interfejsie tabbedowym
- JavaScript nie łączy się z QEMU VNC (port 5901) ani SSH (port 2222)

### 2. **ZŁOŻONOŚĆ ARCHITEKTURY**
- **25+ serwisów** w docker-compose.yml
- **Wielopoziomowe zależności**: każdy HMI serwis zależy od rpi3pc
- **Różne technologie**: JS, Python, PHP, Bash - brak spójności
- **Kompleksowa sieć portów**: 30+ portów w .env

### 3. **PROBLEMY DIAGNOSTYCZNE**
- Trudno śledzić przepływ danych między serwisami
- Brak centralnego monitoringu zmiennych środowiskowych
- Żadne narzędzie do debugowania połączeń I2C/RS232/USB
- Rozproszenie logów w wielu kontenerach

### 4. **NADMIAROWOŚĆ TECHNOLOGII**
- **3 różne implementacje RPi**: rpi, rpi3pc, rpi-qemu
- **JavaScript dla wszystkich HMI** zamiast prostszego PHP
- **QEMU** może być overkill dla prostych testów diagnostycznych

## Proponowana Uproszczona Architektura

### 1. **JEDNOLITY DASHBOARD PHP (Port 8060)**

```php
<?php
// dashboard/index.php - Główny punkt sterowania
require_once 'config.php';
require_once 'services.php';

class C20Dashboard {
    private $services;
    private $env_vars;
    
    public function __construct() {
        $this->loadEnvironment();
        $this->initServices();
    }
    
    public function showRPI3Status() {
        return [
            'qemu_status' => $this->checkQEMUStatus(),
            'vnc_connection' => $this->testVNC(),
            'ssh_connection' => $this->testSSH(),
            'boot_progress' => $this->getBootProgress()
        ];
    }
}
?>
```

### 2. **UPROSZCZONY STOS SERWISÓW**

```yaml
# Simplified docker-compose.yml
version: '3.8'

services:
  # === CORE SERVICES ===
  dashboard:
    build: ./dashboard
    ports: ["8060:80"]
    volumes: [".env:/var/www/html/.env"]
    
  # === RPI SIMULATION ===
  rpi-sim:
    build: ./rpi-simulation
    ports: 
      - "2222:22"    # SSH
      - "5901:5901"  # VNC  
      - "4000:4000"  # API
    environment:
      - MODE=diagnostic  # Simplified mode
      
  # === HARDWARE SIMULATION ===
  hw-bridge:
    build: ./hardware-bridge
    ports: ["8061:80"]
    devices: ["/dev/i2c-1", "/dev/ttyUSB0", "/dev/ttyAMA0"]
    
  # === MQTT (unchanged) ===
  mqtt:
    image: eclipse-mosquitto:2.0
    ports: ["1883:1883", "9001:9001"]
```

### 3. **INTEGRACJA RPI3 W HMI-MONITOR**

```php
<?php
// hmi-monitor/rpi3-viewer.php
class RPI3Viewer {
    private $vnc_url;
    private $ssh_connection;
    
    public function __construct() {
        $this->vnc_url = "ws://localhost:5901";
        $this->ssh_connection = new SSH2('localhost', 2222);
    }
    
    public function showBootProcess() {
        echo "<div class='rpi3-boot-monitor'>";
        echo "<h3>RPI3 Boot Process</h3>";
        
        // VNC Display
        echo "<div class='vnc-display'>";
        echo "<canvas id='rpi3-screen' width='1920' height='1080'></canvas>";
        echo "</div>";
        
        // Boot Progress
        echo "<div class='boot-progress'>";
        $boot_log = $this->getBootLog();
        foreach($boot_log as $line) {
            echo "<div class='boot-line'>$line</div>";
        }
        echo "</div>";
        
        echo "</div>";
    }
    
    private function getBootLog() {
        // SSH connection to get dmesg
        return $this->ssh_connection->exec('dmesg | tail -20');
    }
}
?>
```

### 4. **HARDWARE BRIDGE - STANDARDYZACJA PORTÓW**

```python
# hardware-bridge/main.py
import asyncio
import json
from typing import Dict, Any

class HardwareBridge:
    """Unified hardware interface for all standard ports"""
    
    def __init__(self):
        self.i2c_devices = {}
        self.serial_ports = {}
        self.usb_devices = {}
        self.video_outputs = {}
        
    async def scan_hardware(self) -> Dict[str, Any]:
        """Scan all available hardware interfaces"""
        return {
            'i2c': await self.scan_i2c(),
            'serial': await self.scan_serial(),
            'usb': await self.scan_usb(),
            'video': await self.scan_video()
        }
    
    async def scan_i2c(self):
        """Scan I2C bus for devices"""
        devices = []
        for addr in range(0x08, 0x78):
            try:
                # Test I2C device presence
                result = await self.test_i2c_device(addr)
                if result:
                    devices.append({
                        'address': hex(addr),
                        'status': 'active',
                        'type': self.identify_device(addr)
                    })
            except:
                continue
        return devices
    
    async def scan_serial(self):
        """Scan serial ports (RS232, UART)"""
        import serial.tools.list_ports
        ports = []
        for port in serial.tools.list_ports.comports():
            ports.append({
                'device': port.device,
                'description': port.description,
                'hwid': port.hwid,
                'status': 'available'
            })
        return ports
```

### 5. **UPROSZCZONY MONITORING ZMIENNYCH**

```php
<?php
// dashboard/env-monitor.php
class EnvironmentMonitor {
    private $env_file = '.env';
    private $services_status = [];
    
    public function getEnvironmentDashboard() {
        $vars = $this->parseEnvFile();
        $services = $this->getServicesStatus();
        
        echo "<div class='env-dashboard'>";
        echo "<h2>Environment Variables & Services Status</h2>";
        
        // Port mapping table
        echo "<table class='port-table'>";
        echo "<tr><th>Service</th><th>Port</th><th>Status</th><th>URL</th></tr>";
        
        foreach($vars as $key => $value) {
            if(strpos($key, '_PORT') !== false) {
                $service = str_replace('_PORT', '', $key);
                $status = $this->checkServiceStatus($value);
                $url = "http://localhost:$value";
                
                echo "<tr>";
                echo "<td>$service</td>";
                echo "<td>$value</td>";
                echo "<td class='status-$status'>$status</td>";
                echo "<td><a href='$url' target='_blank'>$url</a></td>";
                echo "</tr>";
            }
        }
        echo "</table>";
        echo "</div>";
    }
    
    private function checkServiceStatus($port) {
        $connection = @fsockopen('localhost', $port, $errno, $errstr, 1);
        if($connection) {
            fclose($connection);
            return 'online';
        }
        return 'offline';
    }
}
?>
```

## Lepsze Rozwiązania dla Symulacji Sprzętowej

### 1. **Frameworki do Symulacji Hardware**

```python
# hardware-sim/device_simulator.py
import asyncio
from enum import Enum
from dataclasses import dataclass

class PortType(Enum):
    I2C = "i2c"
    RS232 = "rs232" 
    USB = "usb"
    HDMI = "hdmi"
    DVI = "dvi"
    GPIO = "gpio"

@dataclass
class SimulatedDevice:
    name: str
    port_type: PortType
    address: str
    data_handler: callable

class UniversalDeviceSimulator:
    """Universal simulator for all hardware interfaces"""
    
    def __init__(self):
        self.devices = {}
        self.port_handlers = {
            PortType.I2C: self.handle_i2c,
            PortType.RS232: self.handle_rs232,
            PortType.USB: self.handle_usb,
            PortType.HDMI: self.handle_video,
            PortType.DVI: self.handle_video,
        }
    
    def register_device(self, device: SimulatedDevice):
        """Register a simulated device"""
        self.devices[device.address] = device
        print(f"Registered {device.name} on {device.port_type.value}:{device.address}")
    
    async def handle_i2c(self, address: str, data: bytes):
        """Handle I2C communication"""
        if address in self.devices:
            device = self.devices[address]
            return await device.data_handler(data)
        return b'\x00'  # Default response
    
    # Similar handlers for other port types...
```

### 2. **Narzędzia Diagnostyczne**

```bash
#!/bin/bash
# tools/diagnose.sh - Unified diagnostic tool

echo "=== C20 System Diagnostics ==="

# Check all services
echo "1. Service Status:"
docker-compose ps

echo "2. Port Status:"
netstat -tlnp | grep -E ':(8060|8061|4000|2222|5901|1883)'

echo "3. Hardware Interfaces:"
ls -la /dev/i2c* /dev/ttyUSB* /dev/ttyAMA* 2>/dev/null

echo "4. Environment Variables:"
grep -E '_PORT=' .env | sort

echo "5. RPI3 Status:"
curl -s http://localhost:4000/api/status || echo "RPI3 API not responding"

echo "6. VNC Connection Test:"
nc -zv localhost 5901 && echo "VNC OK" || echo "VNC Failed"

echo "7. SSH Connection Test:"  
nc -zv localhost 2222 && echo "SSH OK" || echo "SSH Failed"
```

## Implementacja - Krok po Kroku

### Krok 1: Utworzenie Dashboard PHP

```bash
mkdir -p dashboard
cd dashboard
```

### Krok 2: Integracja RPI3 w HMI-Monitor

```php
// Dodanie zakładki RPI3 w hmi-monitor
echo "<div class='tab-content' id='rpi3-tab'>";
include 'rpi3-viewer.php';
$viewer = new RPI3Viewer();
$viewer->showBootProcess();
echo "</div>";
```

### Krok 3: Uproszczenie docker-compose.yml

```yaml
# Redukcja z 25+ do 4 głównych serwisów
services:
  dashboard, rpi-sim, hw-bridge, mqtt
```

## Korzyści z Uproszczenia

1. **Łatwiejsza diagnostyka** - wszystko w jednym dashboard
2. **Mniej zależności** - 4 serwisy zamiast 25+
3. **Jednolita technologia** - PHP + Python zamiast mix technologii
4. **Lepsze monitorowanie** - realtime status wszystkich portów
5. **Prostsze debugowanie** - scentralizowane logi i status

## Pytanie do Implementacji

Czy chcesz żebym zaczął implementację od:
1. **Dashboard PHP z integracją RPI3** (pokazywanie boot process)
2. **Uproszczenia docker-compose** (redukcja serwisów)  
3. **Hardware Bridge** (standaryzacja portów)
4. **Narzędzi diagnostycznych** (unified monitoring)

Które rozwiązanie jest priorytetem?
