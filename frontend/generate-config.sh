#!/bin/sh
set -e

echo "Generating config.json from environment variables..."

# Read HOST_DOMAIN from environment, default to localhost
HOST_DOMAIN=${HOST_DOMAIN:-localhost}

# Read port variables from environment
LCD_DISPLAY_PORT=${LCD_DISPLAY_PORT:-8089}
HUI_KEYBOARD_PORT=${HUI_KEYBOARD_PORT:-8087}
MODBUS_VISUALIZER_PORT=${MODBUS_VISUALIZER_PORT:-8084}
MODBUS_IO_API_PORT=${MODBUS_IO_API_PORT:-8085}
RPI_API_PORT=${RPI_API_PORT:-4000}
HMI_PAD_PORT=${HMI_PAD_PORT:-8086}
HMI_KEYBOARD_PORT=${HMI_KEYBOARD_PORT:-8073}
HMI_MONITOR_PORT=${HMI_MONITOR_PORT:-8072}
HMI_NUMPAD_PORT=${HMI_NUMPAD_PORT:-8074}
MQTT_WEBSOCKET_PORT=${MQTT_WEBSOCKET_PORT:-9001}

# Generate config.json
cat > /usr/share/nginx/html/config.json << EOF
{
  "app": {
    "name": "C20 Hardware Simulator",
    "version": "1.0",
    "title": "C20 Digital Twin Dashboard"
  },
  "services": {
    "lcd_display": {
      "name": "LCD Display",
      "url": "http://${HOST_DOMAIN}:${LCD_DISPLAY_PORT}",
      "icon": "fas fa-desktop",
      "description": "7.9\" HDMI Display Simulator"
    },
    "hui_keyboard": {
      "name": "HUI Keyboard Panel",
      "url": "http://${HOST_DOMAIN}:${HUI_KEYBOARD_PORT}",
      "icon": "fas fa-keyboard",
      "description": "Interactive Keyboard Interface"
    },
    "modbus_visualizer": {
      "name": "Modbus I/O Visualizer",
      "url": "http://${HOST_DOMAIN}:${MODBUS_VISUALIZER_PORT}",
      "icon": "fas fa-network-wired",
      "description": "Real-time Modbus Data Visualization"
    },
    "modbus_io_api": {
      "name": "Modbus IO API",
      "url": "http://${HOST_DOMAIN}:${MODBUS_IO_API_PORT}",
      "icon": "fas fa-api",
      "description": "Modbus RTU IO 8CH API"
    },
    "rpi_api": {
      "name": "RPi Emulator API",
      "url": "http://${HOST_DOMAIN}:${RPI_API_PORT}",
      "icon": "fas fa-microchip",
      "description": "Raspberry Pi Hardware Emulator"
    },
    "hmi_pad": {
      "name": "HMI Virtual Touchpad",
      "url": "http://${HOST_DOMAIN}:${HMI_PAD_PORT}",
      "icon": "fas fa-hand-pointer",
      "description": "Virtual Touchpad Interface for RPi Control"
    },
    "hmi_keyboard": {
      "name": "HMI Virtual Keyboard",
      "url": "http://${HOST_DOMAIN}:${HMI_KEYBOARD_PORT}",
      "icon": "fas fa-keyboard",
      "description": "Virtual Keyboard Interface for RPi Input"
    },
    "hmi_monitor": {
      "name": "HMI Virtual Monitor",
      "url": "http://${HOST_DOMAIN}:${HMI_MONITOR_PORT}",
      "icon": "fas fa-desktop",
      "description": "Virtual HDMI Monitor for RPi Display Output"
    },
    "hmi_numpad": {
      "name": "HMI Virtual Numpad",
      "url": "http://${HOST_DOMAIN}:${HMI_NUMPAD_PORT}",
      "icon": "fas fa-calculator",
      "description": "Virtual Numpad Interface for RPi Numeric Input"
    }
  },
  "mqtt": {
    "broker_url": "ws://${HOST_DOMAIN}:${MQTT_WEBSOCKET_PORT}",
    "broker_port": 1883,
    "topics": {
      "sensors": "c20/sensors",
      "actuators": "c20/actuators",
      "status": "c20/status"
    }
  },
  "ui": {
    "refresh_interval": 5000,
    "enable_debug": false,
    "theme": "default",
    "layouts": ["grid", "tabs", "focus"],
    "default_layout": "grid"
  }
}
EOF

echo "config.json generated successfully with current environment variables"
