# Uproszczona Architektura Modularna C20 Hardware Simulator

## 🎯 Cel uproszczenia
Stworzenie modularnej architektury, gdzie każdy komponent może być łatwo wymieniony, aktualizowany lub usunięty bez wpływu na inne części systemu.

## 📋 Obecne problemy do rozwiązania

### Problemy z kontenerami:
- **HMI kontenery:** `start.sh` nie znaleziony (hmi-numpad, hmi-keyboard, hmi-pad)
- **Modbus IO:** Błędy importu Python (`ImportError: cannot import name 'web_app'`)
- **Złożoność:** 14+ oddzielnych kontenerów z różnymi zależnościami

## 🏗️ Proponowana uproszczona struktura

### 1. Grupy funkcjonalne zamiast pojedynczych kontenerów

```
STARA STRUKTURA (14 kontenerów):
├── hmi-pad (8070)          ❌ Exited (127)
├── hmi-keyboard (8071)     ❌ Exited (127) 
├── hmi-monitor (8072)      ✅ Up
├── hmi-numpad (8073)       ❌ Exited (127)
├── modbus-io-8ch (8085)    ❌ Exited (1)
├── modbus-visualizer (8084) ✅ Up
├── lcd-display (8089)      ✅ Up
├── hui-keyboard (8087)     ✅ Up
├── rpi3pc (4000)          ✅ Up
├── rpi-qemu (unhealthy)   ⚠️ Up (unhealthy)
├── mqtt (1883, 9001)      ✅ Up
├── frontend (8088)        ✅ Up
└── + pozostałe serwisy...
```

```
NOWA STRUKTURA (6 głównych modułów):
├── core-services/         # MQTT, Config, Logs
├── rpi-emulation/         # RPi3PC, QEMU, API
├── hmi-suite/             # Wszystkie HMI w jednym kontenerze
├── display-services/      # LCD, HUI, Visualizers  
├── io-services/           # Modbus, Sensors, Valves
└── web-dashboard/         # Unified Frontend
```

### 2. Standardyzowane szablony kontenerów

#### Szablon A: Usługa z backendem Python + nginx
```yaml
services:
  service-name:
    build:
      context: ./services/service-name
      dockerfile: Dockerfile.standard-python
    environment:
      - SERVICE_NAME=service-name
      - SERVICE_PORT=80
      - BACKEND_PORT=5000
    volumes:
      - ./services/service-name/config:/app/config
    networks: [c20-network]
```

#### Szablon B: Tylko frontend (statyczny)
```yaml
services:
  service-name:
    build:
      context: ./services/service-name  
      dockerfile: Dockerfile.standard-static
    environment:
      - SERVICE_NAME=service-name
    networks: [c20-network]
```

### 3. Wspólne komponenty

#### Shared libs (`/shared/`):
- `common/logger.py` - Standardowy logger Python
- `common/mqtt_client.py` - MQTT wrapper
- `common/config_loader.py` - Ładowanie .env
- `common/health_check.py` - Health check endpoint

#### Template Dockerfiles:
- `templates/Dockerfile.python-nginx` - Python backend + nginx
- `templates/Dockerfile.static-only` - Tylko statyczne pliki
- `templates/docker-entrypoint.sh` - Standardowy entrypoint

### 4. Uproszczone zarządzanie

#### Makefile z prostymi komendami:
```makefile
# Budowanie grup serwisów
build-core:      # Buduj core services
build-hmi:       # Buduj wszystkie HMI
build-display:   # Buduj display services
build-io:        # Buduj IO services

# Zarządzanie
start-essential: # Start tylko kluczowych serwisów
start-full:      # Start wszystkich serwisów
restart-hmi:     # Restart tylko HMI
health-check:    # Sprawdź status wszystkich
```

#### Profile docker-compose:
```yaml
profiles:
  - essential    # MQTT, RPi, Dashboard
  - development  # + HMI, Display  
  - full         # Wszystkie serwisy
```

## 🔧 Plan implementacji

### Faza 1: Napraw obecne problemy
1. ✅ Diagnoza problemów kontenerów
2. 🔄 Przebudowa problematycznych kontenerów HMI
3. 🔄 Naprawa Modbus IO importów

### Faza 2: Grupowanie serwisów
1. Połącz HMI kontenery w `hmi-suite`
2. Utwórz `display-services` (LCD + HUI + Visualizer)
3. Skonsoliduj `io-services` (Modbus + Sensors)

### Faza 3: Standardyzacja
1. Stwórz template Dockerfiles
2. Ujednolic konfigurację (shared libs)
3. Uprosć docker-compose.yml

### Faza 4: Łatwość wymiany
1. Plugin system dla nowych komponentów
2. Standardowe API między serwisami
3. Hot-reload configuration

## 📊 Korzyści

### Przed uproszczeniem:
- ❌ 14+ osobnych kontenerów  
- ❌ Różne sposoby konfiguracji
- ❌ Trudna diagnostyka problemów
- ❌ Skomplikowane zależności

### Po uproszczeniu:
- ✅ 6 logicznych grup serwisów
- ✅ Standardowe szablony i konfiguracja  
- ✅ Łatwiejsza diagnostyka i logs
- ✅ Plug-and-play komponenty

## 🚀 Natychmiastowe korzyści
1. **Łatwiejsze debugowanie** - mniej kontenerów do sprawdzania
2. **Szybsze uruchamianie** - mniej zależności między kontenerami  
3. **Proste skalowanie** - dodaj nowy serwis kopiując szablon
4. **Consistency** - wszystkie serwisy używają tych samych wzorców
