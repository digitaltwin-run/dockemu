#!/usr/bin/env python3
"""
HMI Virtual Numpad Backend
Handles numpad input events, MQTT integration, and forwarding to RPi emulator/QEMU
"""

import asyncio
import websockets
import json
import logging
import time
import threading
from datetime import datetime
import paho.mqtt.client as mqtt

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class VirtualNumpadBackend:
    def __init__(self):
        self.clients = set()
        self.mqtt_client = None
        self.target_devices = {
            'rpi3pc': {'status': 'unknown', 'topic': 'rpi/input/numpad'},
            'rpi-qemu': {'status': 'unknown', 'topic': 'qemu/input/numpad'}
        }
        
        # Statistics
        self.stats = {
            'keys_processed': 0,
            'commands_sent': 0,
            'mqtt_messages': 0,
            'start_time': time.time()
        }
        
        # Setup MQTT
        self.setup_mqtt()

    def setup_mqtt(self):
        """Setup MQTT client for communication with RPi emulator and QEMU"""
        try:
            self.mqtt_client = mqtt.Client(client_id="hmi-numpad")
            self.mqtt_client.on_connect = self.on_mqtt_connect
            self.mqtt_client.on_message = self.on_mqtt_message
            self.mqtt_client.on_disconnect = self.on_mqtt_disconnect
            
            # Connect to MQTT broker
            self.mqtt_client.connect("mqtt", 1883, 60)
            self.mqtt_client.loop_start()
            
            logger.info("MQTT client initialized")
        except Exception as e:
            logger.error(f"Failed to setup MQTT: {e}")

    def on_mqtt_connect(self, client, userdata, flags, rc):
        """Callback for MQTT connection"""
        if rc == 0:
            logger.info("Connected to MQTT broker")
            # Subscribe to device status topics
            client.subscribe("rpi/status")
            client.subscribe("qemu/status")
            client.subscribe("hmi/numpad/+")
            
            # Broadcast MQTT status to WebSocket clients
            asyncio.create_task(self.broadcast_to_clients({
                'type': 'status_update',
                'mqtt_status': 'connected'
            }))
        else:
            logger.error(f"Failed to connect to MQTT broker: {rc}")

    def on_mqtt_disconnect(self, client, userdata, rc):
        """Callback for MQTT disconnection"""
        logger.warning("Disconnected from MQTT broker")
        asyncio.create_task(self.broadcast_to_clients({
            'type': 'status_update',
            'mqtt_status': 'error'
        }))

    def on_mqtt_message(self, client, userdata, msg):
        """Handle MQTT messages from RPi emulator and QEMU"""
        try:
            topic = msg.topic
            payload = json.loads(msg.payload.decode())
            
            if topic == "rpi/status":
                self.target_devices['rpi3pc']['status'] = payload.get('status', 'unknown')
                self.broadcast_target_status('rpi3pc', payload.get('status', 'unknown'))
                
            elif topic == "qemu/status":
                self.target_devices['rpi-qemu']['status'] = payload.get('status', 'unknown')
                self.broadcast_target_status('rpi-qemu', payload.get('status', 'unknown'))
                
            elif topic.startswith("hmi/numpad/"):
                self.handle_numpad_response(topic, payload)
                
            self.stats['mqtt_messages'] += 1
            
        except Exception as e:
            logger.error(f"Error processing MQTT message: {e}")

    def handle_numpad_response(self, topic, payload):
        """Handle responses from numpad commands"""
        device = topic.split('/')[-1]  # Extract device from topic
        
        asyncio.create_task(self.broadcast_to_clients({
            'type': 'key_acknowledged',
            'target': device,
            'key': payload.get('key'),
            'status': payload.get('status', 'ok')
        }))

    def broadcast_target_status(self, device, status):
        """Broadcast target device status to WebSocket clients"""
        asyncio.create_task(self.broadcast_to_clients({
            'type': 'target_status',
            'device': device,
            'status': status
        }))

    async def handle_websocket_client(self, websocket, path):
        """Handle WebSocket client connections"""
        try:
            self.clients.add(websocket)
            logger.info(f"Numpad client connected: {websocket.remote_address}")
            
            # Send initial status
            await websocket.send(json.dumps({
                'type': 'status_update',
                'mqtt_status': 'connected' if self.mqtt_client and self.mqtt_client.is_connected() else 'error',
                'target_devices': self.target_devices,
                'stats': self.get_stats()
            }))
            
            # Handle messages from client
            async for message in websocket:
                await self.handle_client_message(websocket, json.loads(message))
                
        except websockets.exceptions.ConnectionClosed:
            pass
        except Exception as e:
            logger.error(f"WebSocket client error: {e}")
        finally:
            self.clients.discard(websocket)
            logger.info(f"Numpad client disconnected")

    async def handle_client_message(self, websocket, message):
        """Handle messages from WebSocket clients"""
        try:
            msg_type = message.get('type')
            
            if msg_type == 'key_event':
                await self.handle_key_event(message)
            elif msg_type == 'get_stats':
                await websocket.send(json.dumps({
                    'type': 'stats_update',
                    'stats': self.get_stats()
                }))
            else:
                logger.warning(f"Unknown message type: {msg_type}")
                
        except Exception as e:
            logger.error(f"Error handling client message: {e}")

    async def handle_key_event(self, message):
        """Handle key event from client"""
        try:
            key = message.get('key')
            code = message.get('code')
            action = message.get('action')
            target = message.get('target', 'rpi3pc')
            numlock = message.get('numlock', True)
            data = message.get('data')
            
            # Prepare key event for MQTT
            key_event = {
                'type': 'numpad_input',
                'key': key,
                'code': code,
                'action': action,
                'numlock': numlock,
                'timestamp': message.get('timestamp', time.time() * 1000),
                'source': 'hmi-numpad'
            }
            
            # Add data for input strings
            if data:
                key_event['data'] = data
            
            # Convert numpad keys to appropriate format for RPi
            if action == 'input':
                # Handle input strings
                key_event['input_string'] = data
            else:
                # Handle individual key presses
                key_event['virtual_key'] = self.convert_numpad_key(key, code, numlock)
            
            # Send to appropriate target device via MQTT
            if target in self.target_devices:
                topic = self.target_devices[target]['topic']
                
                if self.mqtt_client and self.mqtt_client.is_connected():
                    self.mqtt_client.publish(topic, json.dumps(key_event))
                    
                    self.stats['keys_processed'] += 1
                    if action == 'input':
                        self.stats['commands_sent'] += 1
                    
                    logger.info(f"Key event sent to {target}: {key} ({action})")
                    
                    # Send acknowledgment back to client
                    await self.broadcast_to_clients({
                        'type': 'key_acknowledged',
                        'target': target,
                        'key': key,
                        'action': action
                    })
                else:
                    logger.error(f"MQTT not connected, cannot send key event")
                    await self.broadcast_to_clients({
                        'type': 'error',
                        'message': 'MQTT not connected'
                    })
            else:
                logger.error(f"Unknown target device: {target}")
                
        except Exception as e:
            logger.error(f"Error handling key event: {e}")

    def convert_numpad_key(self, key, code, numlock):
        """Convert numpad key to virtual key code for RPi"""
        # Map numpad keys to virtual key codes
        key_map = {
            '0': 82 if numlock else 45,  # Insert
            '1': 79 if numlock else 35,  # End
            '2': 80 if numlock else 40,  # Down
            '3': 81 if numlock else 34,  # Page Down
            '4': 75 if numlock else 37,  # Left
            '5': 76 if numlock else 12,  # Clear
            '6': 77 if numlock else 39,  # Right
            '7': 71 if numlock else 36,  # Home
            '8': 72 if numlock else 38,  # Up
            '9': 73 if numlock else 33,  # Page Up
            '.': 83 if numlock else 46,  # Delete
            '/': 181,
            '*': 55,
            '-': 74,
            '+': 78,
            'Enter': 28,
            'NumLock': 69,
            'Backspace': 14
        }
        
        return key_map.get(key, 0)

    async def broadcast_to_clients(self, message):
        """Broadcast message to all connected WebSocket clients"""
        if self.clients:
            disconnected_clients = set()
            for client in self.clients:
                try:
                    await client.send(json.dumps(message))
                except websockets.exceptions.ConnectionClosed:
                    disconnected_clients.add(client)
                except Exception as e:
                    logger.error(f"Error broadcasting to client: {e}")
                    disconnected_clients.add(client)
            
            # Remove disconnected clients
            self.clients -= disconnected_clients

    def get_stats(self):
        """Get current statistics"""
        uptime = time.time() - self.stats['start_time']
        return {
            'keys_processed': self.stats['keys_processed'],
            'commands_sent': self.stats['commands_sent'],
            'mqtt_messages': self.stats['mqtt_messages'],
            'uptime': uptime,
            'clients_connected': len(self.clients)
        }

    def start_stats_updater(self):
        """Start periodic stats update to clients"""
        async def stats_updater():
            while True:
                try:
                    await asyncio.sleep(5)  # Update every 5 seconds
                    await self.broadcast_to_clients({
                        'type': 'stats_update',
                        'stats': self.get_stats()
                    })
                except Exception as e:
                    logger.error(f"Error in stats updater: {e}")
        
        asyncio.create_task(stats_updater())

def main():
    """Main function to start the virtual numpad backend"""
    logger.info("Starting HMI Virtual Numpad Backend...")
    
    # Create backend instance
    backend = VirtualNumpadBackend()
    
    # Start stats updater
    backend.start_stats_updater()
    
    # Start WebSocket server
    async def websocket_handler(websocket, path):
        await backend.handle_websocket_client(websocket, path)
    
    # Start server
    start_server = websockets.serve(websocket_handler, "0.0.0.0", 5560)
    
    logger.info("WebSocket server starting on port 5560")
    
    # Run event loop
    loop = asyncio.get_event_loop()
    loop.run_until_complete(start_server)
    
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        logger.info("Shutting down...")
    finally:
        loop.close()

if __name__ == "__main__":
    main()
