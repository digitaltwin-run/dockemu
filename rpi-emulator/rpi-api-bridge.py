#!/usr/bin/env python3
"""
Raspberry Pi API Bridge
Bridge between QEMU-virtualized Raspberry Pi and the C20 simulator system
"""

import json
import time
import socket
import threading
import subprocess
import os
from flask import Flask, jsonify, request
from flask_cors import CORS
import paho.mqtt.client as mqtt
import websockets
import asyncio
from datetime import datetime

app = Flask(__name__)
CORS(app)

class RPiQEMUBridge:
    def __init__(self):
        self.ssh_host = "localhost"
        self.ssh_port = 2222
        self.ssh_user = "pi"
        self.vnc_port = 5901
        self.mqtt_client = None
        self.websocket_clients = set()
        self.rpi_status = "starting"
        self.gpio_states = {}
        self.hardware_status = {
            "cpu_temp": 0.0,
            "cpu_usage": 0.0,
            "memory_usage": 0.0,
            "disk_usage": 0.0,
            "uptime": 0
        }
        
        self.init_mqtt()
        self.start_status_monitor()

    def init_mqtt(self):
        """Initialize MQTT client"""
        try:
            self.mqtt_client = mqtt.Client()
            self.mqtt_client.on_connect = self.on_mqtt_connect
            self.mqtt_client.on_message = self.on_mqtt_message
            self.mqtt_client.connect("c20-mqtt", 1883, 60)
            self.mqtt_client.loop_start()
        except Exception as e:
            print(f"MQTT connection failed: {e}")

    def on_mqtt_connect(self, client, userdata, flags, rc):
        print(f"MQTT connected with result code {rc}")
        client.subscribe("c20/rpi/+")
        client.subscribe("c20/gpio/+")

    def on_mqtt_message(self, client, userdata, msg):
        try:
            topic = msg.topic
            payload = json.loads(msg.payload.decode())
            
            if topic.startswith("c20/rpi/"):
                self.handle_rpi_command(topic, payload)
            elif topic.startswith("c20/gpio/"):
                self.handle_gpio_command(topic, payload)
                
        except Exception as e:
            print(f"MQTT message error: {e}")

    def handle_rpi_command(self, topic, payload):
        """Handle RPI-specific commands"""
        command = topic.split("/")[-1]
        
        if command == "reboot":
            self.reboot_rpi()
        elif command == "shutdown":
            self.shutdown_rpi()
        elif command == "execute":
            self.execute_ssh_command(payload.get("command", ""))

    def handle_gpio_command(self, topic, payload):
        """Handle GPIO commands"""
        pin = topic.split("/")[-1]
        
        if payload.get("action") == "set":
            self.set_gpio_pin(pin, payload.get("value", 0))
        elif payload.get("action") == "read":
            self.read_gpio_pin(pin)

    def execute_ssh_command(self, command):
        """Execute command on Raspberry Pi via SSH"""
        try:
            ssh_cmd = [
                "ssh", "-p", str(self.ssh_port),
                "-o", "StrictHostKeyChecking=no",
                "-o", "UserKnownHostsFile=/dev/null",
                f"{self.ssh_user}@{self.ssh_host}",
                command
            ]
            
            result = subprocess.run(ssh_cmd, capture_output=True, text=True, timeout=30)
            
            response = {
                "command": command,
                "returncode": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "timestamp": datetime.now().isoformat()
            }
            
            if self.mqtt_client:
                self.mqtt_client.publish("c20/rpi/command_result", json.dumps(response))
                
            return response
            
        except Exception as e:
            error_response = {
                "command": command,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
            
            if self.mqtt_client:
                self.mqtt_client.publish("c20/rpi/command_error", json.dumps(error_response))
                
            return error_response

    def set_gpio_pin(self, pin, value):
        """Set GPIO pin value"""
        command = f"echo {value} > /sys/class/gpio/gpio{pin}/value"
        return self.execute_ssh_command(command)

    def read_gpio_pin(self, pin):
        """Read GPIO pin value"""
        command = f"cat /sys/class/gpio/gpio{pin}/value"
        return self.execute_ssh_command(command)

    def reboot_rpi(self):
        """Reboot Raspberry Pi"""
        self.rpi_status = "rebooting"
        return self.execute_ssh_command("sudo reboot")

    def shutdown_rpi(self):
        """Shutdown Raspberry Pi"""
        self.rpi_status = "shutting_down"
        return self.execute_ssh_command("sudo shutdown -h now")

    def check_rpi_connectivity(self):
        """Check if RPi is accessible via SSH"""
        try:
            result = self.execute_ssh_command("echo 'ping'")
            if result.get("returncode") == 0:
                self.rpi_status = "running"
                return True
            else:
                self.rpi_status = "unreachable"
                return False
        except:
            self.rpi_status = "unreachable"
            return False

    def get_hardware_status(self):
        """Get hardware status from RPi"""
        try:
            # CPU temperature
            temp_result = self.execute_ssh_command("vcgencmd measure_temp")
            if temp_result.get("returncode") == 0:
                temp_str = temp_result.get("stdout", "").strip()
                if "temp=" in temp_str:
                    self.hardware_status["cpu_temp"] = float(temp_str.split("=")[1].replace("'C", ""))

            # CPU usage
            cpu_result = self.execute_ssh_command("top -bn1 | grep 'Cpu(s)' | awk '{print $2}' | cut -d'%' -f1")
            if cpu_result.get("returncode") == 0:
                cpu_str = cpu_result.get("stdout", "").strip()
                if cpu_str:
                    self.hardware_status["cpu_usage"] = float(cpu_str)

            # Memory usage
            mem_result = self.execute_ssh_command("free | grep Mem | awk '{printf \"%.1f\", $3/$2 * 100.0}'")
            if mem_result.get("returncode") == 0:
                mem_str = mem_result.get("stdout", "").strip()
                if mem_str:
                    self.hardware_status["memory_usage"] = float(mem_str)

            # Disk usage
            disk_result = self.execute_ssh_command("df / | tail -1 | awk '{print $5}' | cut -d'%' -f1")
            if disk_result.get("returncode") == 0:
                disk_str = disk_result.get("stdout", "").strip()
                if disk_str:
                    self.hardware_status["disk_usage"] = float(disk_str)

            # Uptime
            uptime_result = self.execute_ssh_command("cat /proc/uptime | cut -d' ' -f1")
            if uptime_result.get("returncode") == 0:
                uptime_str = uptime_result.get("stdout", "").strip()
                if uptime_str:
                    self.hardware_status["uptime"] = float(uptime_str)

        except Exception as e:
            print(f"Error getting hardware status: {e}")

    def start_status_monitor(self):
        """Start background status monitoring"""
        def monitor():
            while True:
                try:
                    self.check_rpi_connectivity()
                    if self.rpi_status == "running":
                        self.get_hardware_status()
                    
                    # Publish status via MQTT
                    if self.mqtt_client:
                        status_data = {
                            "status": self.rpi_status,
                            "hardware": self.hardware_status,
                            "timestamp": datetime.now().isoformat()
                        }
                        self.mqtt_client.publish("c20/rpi/status", json.dumps(status_data))
                    
                    time.sleep(10)  # Update every 10 seconds
                except Exception as e:
                    print(f"Status monitor error: {e}")
                    time.sleep(5)

        thread = threading.Thread(target=monitor, daemon=True)
        thread.start()

# Global bridge instance
bridge = RPiQEMUBridge()

# Flask API endpoints
@app.route('/health')
def health():
    return jsonify({"status": "ok", "service": "rpi-qemu-bridge"})

@app.route('/api/status')
def get_status():
    return jsonify({
        "rpi_status": bridge.rpi_status,
        "hardware": bridge.hardware_status,
        "ssh_port": bridge.ssh_port,
        "vnc_port": bridge.vnc_port,
        "timestamp": datetime.now().isoformat()
    })

@app.route('/api/execute', methods=['POST'])
def execute_command():
    data = request.json
    command = data.get('command', '')
    
    if not command:
        return jsonify({"error": "No command provided"}), 400
    
    result = bridge.execute_ssh_command(command)
    return jsonify(result)

@app.route('/api/gpio/<int:pin>/set', methods=['POST'])
def set_gpio(pin):
    data = request.json
    value = data.get('value', 0)
    
    result = bridge.set_gpio_pin(pin, value)
    return jsonify(result)

@app.route('/api/gpio/<int:pin>/read')
def read_gpio(pin):
    result = bridge.read_gpio_pin(pin)
    return jsonify(result)

@app.route('/api/reboot', methods=['POST'])
def reboot():
    result = bridge.reboot_rpi()
    return jsonify(result)

@app.route('/api/shutdown', methods=['POST'])
def shutdown():
    result = bridge.shutdown_rpi()
    return jsonify(result)

@app.route('/api/vnc_info')
def vnc_info():
    return jsonify({
        "vnc_host": bridge.ssh_host,
        "vnc_port": bridge.vnc_port,
        "vnc_url": f"vnc://{bridge.ssh_host}:{bridge.vnc_port}"
    })

# WebSocket for real-time updates
async def websocket_handler(websocket, path):
    bridge.websocket_clients.add(websocket)
    try:
        await websocket.wait_closed()
    finally:
        bridge.websocket_clients.discard(websocket)

if __name__ == '__main__':
    print("Starting Raspberry Pi QEMU Bridge...")
    print(f"API available on port 4000")
    print(f"SSH to RPi: ssh -p {bridge.ssh_port} pi@{bridge.ssh_host}")
    print(f"VNC to RPi: vnc://{bridge.ssh_host}:{bridge.vnc_port}")
    
    app.run(host='0.0.0.0', port=4000, debug=False)
