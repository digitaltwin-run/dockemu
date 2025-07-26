#!/usr/bin/env python3
"""
NUC12 Intel i5 Emulator API Bridge
Provides REST API and WebSocket interface for NUC12 QEMU emulator control
"""

import asyncio
import json
import logging
import subprocess
import threading
import time
import websockets
from datetime import datetime
from flask import Flask, jsonify, request
from flask_cors import CORS
import paho.mqtt.client as mqtt

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class NUC12EmulatorBridge:
    def __init__(self):
        self.app = Flask(__name__)
        CORS(self.app)
        
        # Configuration
        self.mqtt_broker = "mqtt"  # Docker service name
        self.mqtt_port = 1883
        self.mqtt_client = None
        
        # State tracking
        self.system_stats = {
            "cpu_usage": 0,
            "memory_usage": 0,
            "temperature": 45.0,  # Intel i5 typical temp
            "uptime": 0,
            "status": "running"
        }
        
        # WebSocket clients
        self.websocket_clients = set()
        
        self.setup_routes()
        self.setup_mqtt()
        
    def setup_routes(self):
        """Setup Flask REST API routes"""
        
        @self.app.route('/health', methods=['GET'])
        def health():
            return jsonify({
                "status": "healthy",
                "emulator": "NUC12-i5",
                "arch": "x86_64",
                "timestamp": datetime.now().isoformat()
            })
            
        @self.app.route('/status', methods=['GET'])
        def status():
            return jsonify({
                "emulator": "NUC12 Intel i5",
                "architecture": "x86_64",
                "machine": "pc-q35-7.2",
                "cpu": "Intel i5 equivalent (Skylake-Client-v2)",
                "memory": "4GB",
                "cores": 4,
                "threads": 8,
                "stats": self.system_stats,
                "ports": {
                    "ssh": 2223,
                    "vnc": 5902,
                    "api": 4002,
                    "web": 8082
                }
            })
            
        @self.app.route('/keyboard/send', methods=['POST'])
        def send_keyboard():
            data = request.get_json()
            if not data or 'key' not in data:
                return jsonify({"error": "Missing 'key' parameter"}), 400
                
            key = data['key']
            success = self.send_key_to_nuc12(key)
            
            return jsonify({
                "success": success,
                "key_sent": key,
                "timestamp": datetime.now().isoformat()
            })
            
        @self.app.route('/command/execute', methods=['POST'])
        def execute_command():
            data = request.get_json()
            if not data or 'command' not in data:
                return jsonify({"error": "Missing 'command' parameter"}), 400
                
            command = data['command']
            result = self.execute_ssh_command(command)
            
            return jsonify({
                "command": command,
                "result": result,
                "timestamp": datetime.now().isoformat()
            })
            
    def setup_mqtt(self):
        """Setup MQTT client for HMI integration"""
        try:
            self.mqtt_client = mqtt.Client()
            self.mqtt_client.on_connect = self.on_mqtt_connect
            self.mqtt_client.on_message = self.on_mqtt_message
            
            self.mqtt_client.connect(self.mqtt_broker, self.mqtt_port, 60)
            self.mqtt_client.loop_start()
            
        except Exception as e:
            logger.error(f"Failed to setup MQTT: {e}")
            
    def on_mqtt_connect(self, client, userdata, flags, rc):
        """MQTT connection callback"""
        if rc == 0:
            logger.info("Connected to MQTT broker")
            # Subscribe to HMI keyboard topics
            client.subscribe("hmi/keyboard/+")
            client.subscribe("hmi/numpad/+")
        else:
            logger.error(f"Failed to connect to MQTT broker: {rc}")
            
    def on_mqtt_message(self, client, userdata, msg):
        """Handle incoming MQTT messages from HMI devices"""
        try:
            topic = msg.topic
            payload = msg.payload.decode('utf-8')
            
            logger.info(f"MQTT message: {topic} -> {payload}")
            
            if 'keyboard' in topic or 'numpad' in topic:
                # Parse keyboard input
                data = json.loads(payload)
                if 'key' in data:
                    self.send_key_to_nuc12(data['key'])
                    
        except Exception as e:
            logger.error(f"Error processing MQTT message: {e}")
            
    def send_key_to_nuc12(self, key):
        """Send keyboard input to NUC12 via QEMU monitor"""
        try:
            # Convert key to QEMU sendkey format
            qemu_key = self.convert_key_to_qemu(key)
            
            # Send key via QEMU monitor (socat to monitor socket)
            cmd = f"echo 'sendkey {qemu_key}' | socat - unix-connect:/tmp/nuc12-monitor.sock"
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info(f"Sent key to NUC12: {key} -> {qemu_key}")
                self.broadcast_to_websockets({
                    "type": "key_sent",
                    "key": key,
                    "qemu_key": qemu_key,
                    "timestamp": datetime.now().isoformat()
                })
                return True
            else:
                logger.error(f"Failed to send key: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"Error sending key to NUC12: {e}")
            return False
            
    def convert_key_to_qemu(self, key):
        """Convert HMI key to QEMU sendkey format"""
        key_mappings = {
            # Numbers
            '0': '0', '1': '1', '2': '2', '3': '3', '4': '4',
            '5': '5', '6': '6', '7': '7', '8': '8', '9': '9',
            
            # Letters
            'a': 'a', 'b': 'b', 'c': 'c', 'd': 'd', 'e': 'e',
            'f': 'f', 'g': 'g', 'h': 'h', 'i': 'i', 'j': 'j',
            'k': 'k', 'l': 'l', 'm': 'm', 'n': 'n', 'o': 'o',
            'p': 'p', 'q': 'q', 'r': 'r', 's': 's', 't': 't',
            'u': 'u', 'v': 'v', 'w': 'w', 'x': 'x', 'y': 'y', 'z': 'z',
            
            # Special keys
            'Enter': 'ret',
            'Backspace': 'backspace',
            'Space': 'spc',
            'Tab': 'tab',
            'Escape': 'esc',
            'Delete': 'delete',
            'ArrowUp': 'up',
            'ArrowDown': 'down',
            'ArrowLeft': 'left',
            'ArrowRight': 'right',
            
            # Function keys
            'F1': 'f1', 'F2': 'f2', 'F3': 'f3', 'F4': 'f4',
            'F5': 'f5', 'F6': 'f6', 'F7': 'f7', 'F8': 'f8',
            'F9': 'f9', 'F10': 'f10', 'F11': 'f11', 'F12': 'f12',
            
            # Modifiers
            'Shift': 'shift',
            'Control': 'ctrl',
            'Alt': 'alt',
        }
        
        return key_mappings.get(key, key.lower())
        
    def execute_ssh_command(self, command):
        """Execute command on NUC12 via SSH"""
        try:
            ssh_cmd = f"ssh -p 2223 -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null user@localhost '{command}'"
            result = subprocess.run(ssh_cmd, shell=True, capture_output=True, text=True, timeout=30)
            
            return {
                "exit_code": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr
            }
            
        except subprocess.TimeoutExpired:
            return {"error": "Command timeout"}
        except Exception as e:
            return {"error": str(e)}
            
    def broadcast_to_websockets(self, message):
        """Broadcast message to all connected WebSocket clients"""
        if self.websocket_clients:
            disconnected = set()
            for websocket in self.websocket_clients:
                try:
                    asyncio.create_task(websocket.send(json.dumps(message)))
                except:
                    disconnected.add(websocket)
            
            # Remove disconnected clients
            self.websocket_clients -= disconnected
            
    def update_system_stats(self):
        """Update system statistics periodically"""
        while True:
            try:
                # Simulate NUC12 Intel i5 system stats
                import random
                self.system_stats.update({
                    "cpu_usage": random.randint(5, 45),
                    "memory_usage": random.randint(20, 70),
                    "temperature": round(random.uniform(35.0, 65.0), 1),
                    "uptime": int(time.time()),
                    "status": "running"
                })
                
                # Broadcast stats to WebSocket clients
                self.broadcast_to_websockets({
                    "type": "stats_update",
                    "stats": self.system_stats,
                    "timestamp": datetime.now().isoformat()
                })
                
            except Exception as e:
                logger.error(f"Error updating stats: {e}")
                
            time.sleep(10)

def main():
    """Main entry point"""
    logger.info("Starting NUC12 Intel i5 Emulator API Bridge...")
    
    bridge = NUC12EmulatorBridge()
    
    # Start stats update thread
    stats_thread = threading.Thread(target=bridge.update_system_stats, daemon=True)
    stats_thread.start()
    
    # Start Flask API server
    try:
        bridge.app.run(host='0.0.0.0', port=4002, debug=False)
    except KeyboardInterrupt:
        logger.info("Shutting down NUC12 API Bridge...")
    except Exception as e:
        logger.error(f"Error running API server: {e}")

if __name__ == "__main__":
    main()
