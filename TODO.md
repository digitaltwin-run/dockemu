Na podstawie analizy dokumentacji projektu C20 i Twoich wymagań, stworzyłem kompletne rozwiązanie symulacyjne z działającymi przykładami. Oto struktura projektu:

## 🚀 Symulator Sprzętu C20 - Docker Environment

### Struktura projektu:

```
c20-hardware-simulator/
├── docker-compose.yml
├── rpi-emulator/
│   ├── Dockerfile
│   ├── boot.sh
│   └── hardware/
│       ├── i2c_bus.py
│       ├── gpio_controller.py
│       └── modbus_simulator.py
├── lcd-display/
│   ├── Dockerfile
│   ├── index.html
│   ├── app.js
│   └── style.css
├── hui-keyboard/
│   ├── Dockerfile
│   ├── index.html
│   └── server.py
├── pressure-sensors/
│   ├── Dockerfile
│   └── sensors.py
├── valve-controller/
│   ├── Dockerfile
│   └── pcb_out_12.py
├── test-procedures/
│   ├── Dockerfile
│   └── bls_tests.py
└── shared/
    └── protocols/
        └── c20_protocol.py
```

## 8️⃣ Uruchomienie systemu

### Kroki instalacji:

1. **Sklonuj repozytorium:**
```bash
git clone https://github.com/yourusername/c20-hardware-simulator.git
cd c20-hardware-simulator
```

2. **Zbuduj i uruchom kontenery:**
```bash
docker-compose up --build
```

3. **Dostęp do interfejsów:**
- LCD Display: http://localhost:8081
- HUI Keyboard: http://localhost:8082
- WebGUI: http://localhost:8080
- MQTT Broker: localhost:1883

### Przykłady użycia:

#### Test komunikacji I2C:
```python
# W kontenerze rpi
python3 -c "
from hardware.i2c_bus import I2CBusSimulator
import asyncio

async def test():
    bus = I2CBusSimulator()
    # Odczyt z czujnika ciśnienia
    data = await bus.read(0x48, 2)
    print(f'Pressure: {int.from_bytes(data, "big")} mbar')

asyncio.run(test())
"
```

#### Uruchomienie procedury testowej:
```bash
# Przez API
curl -X POST http://localhost:8080/api/procedures/start \
  -H "Content-Type: application/json" \
  -d '{"procedure": "BLS_5000_TEST", "serial": "SN123456"}'
```

## 📝 Podsumowanie

To rozwiązanie zapewnia:

1. **Pełną symulację sprzętu** - wszystkie komponenty C20 jako kontenery
2. **Modularność** - łatwa wymiana i testowanie komponentów
3. **Realistyczne interfejsy** - webowe LCD i klawiatura
4. **Komunikację przez magistrale** - I2C, GPIO, Modbus
5. **Gotowe procedury testowe** - implementacje dla masek BLS
6. **Integrację z projektem C20** - zgodność z dokumentacją









## 🚀 Uruchomienie

1. **Dodaj nowe moduły do projektu:**
```bash
cd c20-hardware-simulator
mkdir -p modbus-io-8ch modbus-visualizer python-control
# Skopiuj pliki do odpowiednich katalogów
```

2. **Uruchom kontenery:**
```bash
docker-compose up --build modbus-io-8ch modbus-visualizer
```

3. **Otwórz wizualizację:**
- http://localhost:8084 - Wizualizacja Modbus IO

4. **Uruchom testy Python:**
```bash
cd python-control
python3 modbus_client.py
python3 test_procedures.py
```

## 📊 Funkcjonalności

System zapewnia:

1. **Pełną symulację protokołu Modbus RTU** zgodną z dokumentacją Waveshare
2. **Wizualizację graficzną** w przeglądarce z kontrolą wszystkich kanałów
3. **API REST** do integracji z innymi systemami
4. **TCP Bridge** dla łatwego testowania bez sprzętu
5. **Przykłady Python** zgodne z dokumentacją
6. **Integrację z projektem C20** - sterowanie zaworami i czujnikami

To rozwiązanie pozwala na pełną symulację i testowanie urządzeń Modbus RTU bez fizycznego sprzętu! 🎉