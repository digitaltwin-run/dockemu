#!/usr/bin/env python3
"""
HMI Virtual Keyboard Backend
Handles keyboard events and forwards them to RPi emulator/QEMU
"""

import json
import asyncio
import websockets
import logging
from flask import Flask, jsonify, request
from flask_cors import CORS
import threading
import paho.mqtt.client as mqtt
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

class KeyboardEventHandler:
    def __init__(self):
        self.connected_clients = set()
        self.rpi_connection = None
        self.mqtt_client = None
        self.key_states = {}
        self.modifier_states = {
            'shift': False, 'ctrl': False, 'alt': False, 'meta': False
        }
        
        self.init_mqtt()
        
    def init_mqtt(self):
        """Initialize MQTT client for C20 system integration"""
        try:
            self.mqtt_client = mqtt.Client()
            self.mqtt_client.on_connect = self.on_mqtt_connect
            self.mqtt_client.on_message = self.on_mqtt_message
            self.mqtt_client.connect("c20-mqtt", 1883, 60)
            self.mqtt_client.loop_start()
            logger.info("MQTT client connected")
        except Exception as e:
            logger.error(f"MQTT connection failed: {e}")

    def on_mqtt_connect(self, client, userdata, flags, rc):
        logger.info(f"MQTT connected with result code {rc}")
        client.subscribe("c20/keyboard/+")

    def on_mqtt_message(self, client, userdata, msg):
        try:
            topic = msg.topic
            payload = json.loads(msg.payload.decode())
            logger.info(f"MQTT message received: {topic} - {payload}")
        except Exception as e:
            logger.error(f"MQTT message error: {e}")

    async def handle_client(self, websocket, path):
        """Handle WebSocket client connections"""
        logger.info(f"New client connected from {websocket.remote_address}")
        self.connected_clients.add(websocket)
        
        try:
            await websocket.wait_closed()
        except Exception as e:
            logger.error(f"Client connection error: {e}")
        finally:
            self.connected_clients.discard(websocket)
            logger.info("Client disconnected")

    async def handle_keyboard_event(self, websocket, message):
        """Process keyboard events from clients"""
        try:
            event_data = json.loads(message)
            
            # Log the event
            logger.info(f"Keyboard event: {event_data}")
            
            # Update key states
            key = event_data.get('key', '')
            event_type = event_data.get('type', '')
            modifiers = event_data.get('modifiers', {})
            
            if event_type == 'keydown':
                self.key_states[key] = True
                self.modifier_states.update(modifiers)
            elif event_type == 'keyup':
                self.key_states.pop(key, None)
                
            # Forward to RPi emulator
            await self.forward_to_rpi(event_data)
            
            # Publish to MQTT
            self.publish_keyboard_event(event_data)
            
            # Send confirmation back to client
            confirmation = {
                'type': 'confirmation',
                'original_event': event_data,
                'timestamp': datetime.now().isoformat()
            }
            await websocket.send(json.dumps(confirmation))
            
        except Exception as e:
            logger.error(f"Error processing keyboard event: {e}")

    async def forward_to_rpi(self, event_data):
        """Forward keyboard events to RPi emulator/QEMU"""
        try:
            # Connect to RPi WebSocket if not connected
            if not self.rpi_connection:
                await self.connect_to_rpi()
            
            if self.rpi_connection:
                # Convert to RPi format
                rpi_event = self.convert_to_rpi_format(event_data)
                await self.rpi_connection.send(json.dumps(rpi_event))
                logger.info(f"Event forwarded to RPi: {rpi_event}")
                
        except Exception as e:
            logger.error(f"Error forwarding to RPi: {e}")
            self.rpi_connection = None

    async def connect_to_rpi(self):
        """Connect to RPi emulator WebSocket"""
        try:
            # Try connecting to QEMU RPi first, then fallback to emulator
            rpi_urls = [
                "ws://c20-rpi-qemu:4000/ws/keyboard",
                "ws://c20-rpi3pc:4000/ws/keyboard"
            ]
            
            for url in rpi_urls:
                try:
                    self.rpi_connection = await websockets.connect(url)
                    logger.info(f"Connected to RPi at {url}")
                    break
                except Exception as e:
                    logger.warning(f"Failed to connect to {url}: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Failed to connect to any RPi service: {e}")

    def convert_to_rpi_format(self, event_data):
        """Convert keyboard event to RPi-compatible format"""
        return {
            'type': 'keyboard_event',
            'event_type': event_data.get('type', ''),
            'key_code': event_data.get('key', ''),
            'modifiers': event_data.get('modifiers', {}),
            'timestamp': event_data.get('timestamp', datetime.now().isoformat()),
            'source': 'hmi-keyboard'
        }

    def publish_keyboard_event(self, event_data):
        """Publish keyboard event to MQTT"""
        if self.mqtt_client:
            try:
                topic = f"c20/keyboard/{event_data.get('type', 'unknown')}"
                mqtt_payload = {
                    'key': event_data.get('key', ''),
                    'modifiers': event_data.get('modifiers', {}),
                    'timestamp': datetime.now().isoformat(),
                    'device': 'hmi-keyboard'
                }
                
                self.mqtt_client.publish(topic, json.dumps(mqtt_payload))
                logger.info(f"Published to MQTT: {topic}")
                
            except Exception as e:
                logger.error(f"MQTT publish error: {e}")

    def get_status(self):
        """Get current keyboard status"""
        return {
            'connected_clients': len(self.connected_clients),
            'rpi_connected': self.rpi_connection is not None,
            'mqtt_connected': self.mqtt_client is not None,
            'active_keys': list(self.key_states.keys()),
            'modifier_states': self.modifier_states,
            'timestamp': datetime.now().isoformat()
        }

# Global handler instance
handler = KeyboardEventHandler()

# Flask API endpoints
@app.route('/health')
def health():
    return jsonify({"status": "ok", "service": "hmi-keyboard-backend"})

@app.route('/api/status')
def get_status():
    return jsonify(handler.get_status())

@app.route('/api/key_states')
def get_key_states():
    return jsonify({
        'active_keys': list(handler.key_states.keys()),
        'modifier_states': handler.modifier_states
    })

@app.route('/api/send_key', methods=['POST'])
def send_key():
    """API endpoint to send keyboard events programmatically"""
    try:
        data = request.json
        
        # Create keyboard event
        event_data = {
            'type': data.get('type', 'keydown'),
            'key': data.get('key', ''),
            'modifiers': data.get('modifiers', {}),
            'timestamp': datetime.now().isoformat(),
            'source': 'api'
        }
        
        # Process the event
        asyncio.create_task(handler.forward_to_rpi(event_data))
        handler.publish_keyboard_event(event_data)
        
        return jsonify({'status': 'sent', 'event': event_data})
        
    except Exception as e:
        logger.error(f"API send_key error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/send_combo', methods=['POST'])
def send_combo():
    """API endpoint to send key combinations"""
    try:
        data = request.json
        keys = data.get('keys', [])
        
        # Send key down events
        for key in keys:
            event_data = {
                'type': 'keydown',
                'key': key,
                'modifiers': handler.modifier_states.copy(),
                'timestamp': datetime.now().isoformat(),
                'source': 'api_combo'
            }
            asyncio.create_task(handler.forward_to_rpi(event_data))
            handler.publish_keyboard_event(event_data)
        
        # Send key up events (reversed order)
        for key in reversed(keys):
            event_data = {
                'type': 'keyup',
                'key': key,
                'modifiers': handler.modifier_states.copy(),
                'timestamp': datetime.now().isoformat(),
                'source': 'api_combo'
            }
            asyncio.create_task(handler.forward_to_rpi(event_data))
            handler.publish_keyboard_event(event_data)
        
        return jsonify({'status': 'sent', 'combo': keys})
        
    except Exception as e:
        logger.error(f"API send_combo error: {e}")
        return jsonify({'error': str(e)}), 500

# WebSocket server
async def websocket_server():
    """Start WebSocket server for keyboard events"""
    logger.info("Starting WebSocket server on port 5556")
    
    async def handle_message(websocket, path):
        handler.connected_clients.add(websocket)
        logger.info(f"WebSocket client connected: {websocket.remote_address}")
        
        try:
            async for message in websocket:
                await handler.handle_keyboard_event(websocket, message)
        except websockets.exceptions.ConnectionClosed:
            logger.info("WebSocket client disconnected")
        except Exception as e:
            logger.error(f"WebSocket error: {e}")
        finally:
            handler.connected_clients.discard(websocket)
    
    server = await websockets.serve(handle_message, "0.0.0.0", 5556)
    logger.info("WebSocket server started successfully")
    await server.wait_closed()

def run_flask():
    """Run Flask API server"""
    logger.info("Starting Flask API server on port 5557")
    app.run(host='0.0.0.0', port=5557, debug=False)

def run_websocket():
    """Run WebSocket server"""
    asyncio.run(websocket_server())

if __name__ == '__main__':
    logger.info("Starting HMI Keyboard Backend...")
    
    # Start Flask in a separate thread
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    
    # Start WebSocket server in main thread
    try:
        run_websocket()
    except KeyboardInterrupt:
        logger.info("Keyboard backend shutting down...")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
