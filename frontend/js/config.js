// Auto-generated configuration from .env file
// Generated on: 2025-07-27 08:00:44

window.CONFIG = {
    "app": {
        "name": "C20 Hardware Simulator",
        "version": "1.0",
        "title": "C20 Digital Twin Dashboard"
    },
    "env": {
        "FRONTEND_PORT": "8088",
        "LCD_DISPLAY_PORT": "8089",
        "HUI_KEYBOARD_PORT": "8087",
        "MODBUS_VISUALIZER_PORT": "8084",
        "HMI_PAD_PORT": "8070",
        "HMI_KEYBOARD_PORT": "8071",
        "HMI_MONITOR_PORT": "8072",
        "HMI_MONITOR_WS_PORT": "5570",
        "HMI_MONITOR_VNC_PORT": "5571",
        "HMI_NUMPAD_PORT": "8073",
        "HMI_NUMPAD_WS_PORT": "5572",
        "MODBUS_IO_TCP_PORT": "5020",
        "MODBUS_IO_API_PORT": "8085",
        "PRESSURE_SENSORS_PORT": "5001",
        "VALVE_CONTROLLER_PORT": "5002",
        "TEST_PROCEDURES_PORT": "5003",
        "MQTT_PORT": "1883",
        "MQTT_WEBSOCKET_PORT": "9001",
        "RPI_API_PORT": "4000",
        "RPI_VNC_PORT": "5901",
        "QEMU_SSH_PORT": "2222",
        "QEMU_VNC_PORT": "5901",
        "QEMU_API_PORT": "4001",
        "QEMU_WEB_PORT": "8091",
        "COMPOSE_PROJECT_NAME": "c20-simulator",
        "DOCKER_NETWORK": "c20-network",
        "HOST_DOMAIN": "localhost",
        "API_HOST": "localhost",
        "MQTT_HOST": "localhost",
        "WS_HOST": "localhost"
    },
    "services": {
        "lcd_display": {
            "name": "LCD Display",
            "url": "http://localhost:8089",
            "icon": "fas fa-desktop",
            "description": "7.9\" HDMI Display Simulator"
        },
        "hui_keyboard": {
            "name": "HUI Keyboard Panel",
            "url": "http://localhost:8087",
            "icon": "fas fa-keyboard",
            "description": "Interactive Keyboard Interface"
        },
        "modbus_visualizer": {
            "name": "Modbus I/O Visualizer",
            "url": "http://localhost:8084",
            "icon": "fas fa-network-wired",
            "description": "Real-time Modbus Data Visualization"
        },
        "modbus_io_api": {
            "name": "Modbus IO API",
            "url": "http://localhost:8085",
            "icon": "fas fa-api",
            "description": "Modbus RTU IO 8CH API"
        },
        "rpi_api": {
            "name": "RPi Emulator API",
            "url": "http://localhost:4000",
            "icon": "fas fa-microchip",
            "description": "Raspberry Pi Hardware Emulator"
        },
        "hmi_pad": {
            "name": "HMI Virtual Touchpad",
            "url": "http://localhost:8070",
            "icon": "fas fa-hand-pointer",
            "description": "Virtual Touchpad Interface for RPi Control"
        },
        "hmi_keyboard": {
            "name": "HMI Virtual Keyboard",
            "url": "http://localhost:8071",
            "icon": "fas fa-keyboard",
            "description": "Virtual Keyboard Interface for RPi Input"
        },
        "hmi_monitor": {
            "name": "HMI Monitor",
            "url": "http://localhost:8072",
            "icon": "fas fa-desktop",
            "description": "HMI Monitor Interface"
        },
        "hmi_numpad": {
            "name": "HMI Virtual Numpad",
            "url": "http://localhost:8073",
            "icon": "fas fa-calculator",
            "description": "Virtual Numpad Interface"
        }
    },
    "network": {
        "host": "localhost",
        "apiHost": "localhost",
        "mqttHost": "localhost",
        "wsHost": "localhost",
        "mqttPort": "1883",
        "mqttWebSocketPort": "9001"
    },
    "ports": {
        "frontend": "8088",
        "lcdDisplay": "8089",
        "huiKeyboard": "8087",
        "modbusTcp": "5020",
        "modbusApi": "8085",
        "rpiApi": "4000",
        "rpiVnc": "5901"
    }
};

// Convenient access to configuration sections
window.APP_CONFIG = window.CONFIG.app;
window.ENV_CONFIG = window.CONFIG.env;
window.SERVICES_CONFIG = window.CONFIG.services;
window.NETWORK_CONFIG = window.CONFIG.network;
window.PORTS_CONFIG = window.CONFIG.ports;

console.log('Configuration loaded:', window.CONFIG);
