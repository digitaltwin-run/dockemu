# C20 Hardware Simulator - Docker Environment

🚀 **Complete Docker-based simulation environment for C20 hardware components with unified dashboard control**

## 📋 Table of Contents

- [Quick Start](#-quick-start)
- [Project Overview](#-project-overview)
- [Installation](#-installation)
- [Using the Simulations](#-using-the-simulations)
- [Available Services](#-available-services)
- [Makefile Commands](#-makefile-commands)
- [Architecture](#-architecture)
- [Troubleshooting](#-troubleshooting)
- [Development](#-development)

## 🚀 Quick Start

**Get everything running in 3 commands:**

```bash
git clone <repository-url>
cd dockemu
make quick-start
```

Then open **http://localhost:8088** for the unified dashboard! 🎉

## 📖 Project Overview

This project provides a complete Docker-based simulation environment for C20 hardware components, including:

- **LCD Display (7.9" HDMI)** - System interface simulation
- **HUI Keyboard Panel** - Interactive control interface  
- **Pressure Sensors** - LP/MP/HP sensor simulation with I2C
- **Valve Controller** - 12-channel PCB output control
- **Modbus I/O** - 8-channel RTU simulation with web visualization
- **Test Procedures** - Automated BLS mask testing
- **Unified Dashboard** - Control all services from one interface

## 🛠️ Installation

### Prerequisites

- Docker and Docker Compose installed
- At least 4GB RAM available
- Ports 8088-8085 available

### Step-by-Step Setup

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd dockemu
   ```

2. **Build all containers:**
   ```bash
   make build
   ```

3. **Start all services:**
   ```bash
   make up
   ```

4. **Verify everything is running:**
   ```bash
   make status
   ```

## 🎮 Using the Simulations

### Unified Dashboard (Recommended)

**Access:** http://localhost:8088

The unified dashboard provides complete control over all simulators:

#### 🖥️ **Layout Modes**
- **Grid View** - See all simulators at once
- **Tab View** - Switch between simulators
- **Focus View** - Single simulator fullscreen

#### 🎛️ **Control Panel Features**
- Toggle services on/off
- Refresh all frames
- Emergency stop all services
- Real-time system monitoring

#### ⌨️ **Keyboard Shortcuts**
- `Ctrl+1` - Grid layout
- `Ctrl+2` - Tab layout  
- `Ctrl+3` - Focus layout
- `Ctrl+R` - Refresh all
- `Ctrl+F` - Toggle fullscreen
- `Esc` - Exit fullscreen/close modals

### Individual Service Access

#### 🖥️ LCD Display Simulator
**Access:** http://localhost:8081

Simulates the 7.9" HDMI display showing:
- System status information
- Current test procedures
- Sensor readings
- Alarm states

#### ⌨️ HUI Keyboard Panel  
**Access:** http://localhost:8082

Interactive keyboard interface for:
- Navigation through menus
- Test procedure control
- Parameter adjustment
- System configuration

**Usage:**
- Click keys to simulate button presses
- Use function keys for special operations
- Monitor I2C communication status

#### 📊 Modbus I/O Visualizer
**Access:** http://localhost:8084

Real-time visualization of 8-channel Modbus RTU:
- **Input Channels:** Monitor digital inputs
- **Output Channels:** Control digital outputs  
- **Register Values:** View/modify Modbus registers
- **Communication Status:** Connection health

**How to use:**
1. Click output channel buttons to toggle states
2. Monitor input changes in real-time
3. Adjust register values using sliders
4. Export/import configurations

#### 🔬 Test Procedures

**BLS Mask Testing:**
```bash
# Run BLS 5000 test
make shell SERVICE=rpi
python3 /shared/test_procedures.py --test BLS_5000

# Run BLS 8000 test  
python3 /shared/test_procedures.py --test BLS_8000
```

**API Testing:**
```bash
# Start a test procedure via API
curl -X POST http://localhost:8088/api/procedures/start \
  -H "Content-Type: application/json" \
  -d '{"procedure": "BLS_5000_TEST", "serial": "SN123456"}'
```

#### 🌡️ Pressure Sensors

**I2C Communication Test:**
```bash
make shell SERVICE=rpi
python3 -c "
from hardware.i2c_bus import I2CBusSimulator
import asyncio

async def test_sensors():
    bus = I2CBusSimulator()
    # Read LP sensor (0x48)
    lp_data = await bus.read(0x48, 2)
    print(f'LP Pressure: {int.from_bytes(lp_data, \"big\")} mbar')
    
    # Read MP sensor (0x49)  
    mp_data = await bus.read(0x49, 2)
    print(f'MP Pressure: {int.from_bytes(mp_data, \"big\")} mbar')
    
    # Read HP sensor (0x4A)
    hp_data = await bus.read(0x4A, 2)  
    print(f'HP Pressure: {int.from_bytes(hp_data, \"big\")} mbar')

asyncio.run(test_sensors())
"
```

#### ⚡ Valve Controller

**Control 12-channel outputs:**
```bash
make shell SERVICE=rpi
python3 -c "
from hardware.gpio_controller import GPIOController
import time

gpio = GPIOController()
# Turn on valve 1
gpio.set_pin(1, True)
time.sleep(2)
# Turn off valve 1  
gpio.set_pin(1, False)
"
```

## 🌐 Available Services

| Service | Port | Description | Health Check |
|---------|------|-------------|--------------|
| **Unified Dashboard** | 8088 | Main control interface | http://localhost:8088/health |
| **LCD Display** | 8081 | System display simulation | http://localhost:8081 |
| **HUI Keyboard** | 8082 | Interactive keyboard | http://localhost:8082 |
| **Modbus Visual** | 8084 | I/O visualization | http://localhost:8084 |
| **MQTT Broker** | 1883 | Message communication | - |
| **WebSocket** | 9001 | Real-time communication | - |

## 🔧 Makefile Commands

### Basic Operations
```bash
make help           # Show all available commands
make build          # Build all Docker images
make up             # Start all services  
make down           # Stop all services
make restart        # Restart all services
make clean          # Complete cleanup (containers, images, volumes)
```

### Development & Debugging
```bash
make logs                           # Show logs from all services
make logs-service SERVICE=rpi       # Show logs from specific service
make shell SERVICE=rpi              # Open shell in container
make status                         # Show container status
make monitoring                     # Real-time resource monitoring
```

### Testing
```bash
make test-all       # Run all test procedures
make test-bls       # Run BLS mask tests  
make test-modbus    # Test Modbus communication
```

### Utilities
```bash
make install        # Setup project dependencies
make backup         # Create project backup
make dev            # Start in development mode
```

## 🏗️ Architecture

### Component Overview
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  Unified        │    │  LCD Display    │    │  HUI Keyboard   │
│  Dashboard      │    │  (nginx)        │    │  (Flask)        │
│  :8088          │    │  :8081          │    │  :8082          │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
         ┌───────────────────────┼───────────────────────┐
         │                       │                       │
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  RPI Controller │    │  Modbus I/O     │    │  MQTT Broker    │
│  (Python)       │    │  Visualizer     │    │  (Mosquitto)    │
│  I2C/GPIO       │    │  :8084          │    │  :1883/:9001    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  Pressure       │    │  Valve          │    │  Test           │
│  Sensors        │    │  Controller     │    │  Procedures     │
│  (I2C)          │    │  (I2C)          │    │  (Python)       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Communication Protocols
- **I2C Bus**: Inter-device communication simulation
- **MQTT**: Pub/sub messaging between services  
- **WebSocket**: Real-time browser updates
- **HTTP REST**: API endpoints for control
- **Modbus RTU**: Industrial protocol simulation

## 🐛 Troubleshooting

### Common Issues

#### 🔴 Build Failures
```bash
# Clean everything and rebuild
make clean
make build

# Check specific service logs
make logs-service SERVICE=<service-name>
```

#### 🔴 Port Conflicts
```bash
# Check what's using ports
sudo netstat -tulpn | grep :808

# Stop conflicting services
sudo systemctl stop <service-name>
```

#### 🔴 Permission Issues
```bash
# Fix Docker permissions
sudo usermod -aG docker $USER
newgrp docker
```

#### 🔴 Container Won't Start
```bash
# Check container status
make status

# Restart specific service
make restart-service SERVICE=<service-name>

# Emergency stop and restart
make down
make up
```

### Service-Specific Issues

#### LCD Display Not Loading
- Check if port 8081 is available
- Verify nginx container is running: `docker ps | grep lcd`
- Check logs: `make logs-service SERVICE=lcd-display`

#### Keyboard Not Responding  
- Verify Flask server is running on port 8082
- Check I2C communication: `make shell SERVICE=rpi`
- Test keyboard service: `curl http://localhost:8082/health`

#### Modbus Communication Issues
- Verify Modbus simulator is listening on port 8084
- Check TCP bridge: `telnet localhost 5020`
- Test register access via API

## 👨‍💻 Development

### Adding New Services

1. **Create service directory:**
   ```bash
   mkdir new-service
   cd new-service
   ```

2. **Add Dockerfile and code**

3. **Update docker-compose.yml:**
   ```yaml
   new-service:
     build: ./new-service
     container_name: c20-new-service
     ports:
       - "8086:80"
     networks:
       - c20-network
   ```

4. **Update unified dashboard** to include new service iframe

### Protocol Extension

The C20 protocol (`shared/protocols/c20_protocol.py`) can be extended with:
- New message types
- Additional device types  
- Custom data structures
- Enhanced error handling

### Testing

```bash
# Run unit tests
make shell SERVICE=rpi
python3 -m pytest /app/tests/ -v

# Integration tests
make test-all

# Load testing
make monitoring  # Monitor during tests
```

---

## 📞 Support

For issues and questions:
- Check the troubleshooting section above
- Review service logs: `make logs`
- Test individual components
- Verify all prerequisites are met

**Happy simulating! 🎉**
