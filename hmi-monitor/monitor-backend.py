#!/usr/bin/env python3
"""
HMI Virtual Monitor Backend
Handles VNC streaming, monitor control, and hardware emulation for RPi HDMI interface
"""

import asyncio
import websockets
import json
import logging
import subprocess
import os
import time
import threading
from datetime import datetime
import paho.mqtt.client as mqtt
from PIL import Image, ImageDraw
import cv2
import numpy as np

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class VirtualMonitorBackend:
    def __init__(self):
        self.clients = set()
        self.vnc_clients = set()
        self.mqtt_client = None
        self.current_resolution = {'width': 1920, 'height': 1080}
        self.refresh_rate = 60
        self.input_source = 'hdmi1'
        self.is_powered = True
        self.is_capturing = False
        
        # VNC connection settings
        self.vnc_host = 'localhost'
        self.vnc_port = 5901
        self.vnc_connected = False
        
        # Frame statistics
        self.frame_stats = {
            'frames_sent': 0,
            'fps': 0,
            'latency': 0,
            'data_rate': 0
        }
        
        # Setup MQTT
        self.setup_mqtt()
        
        # Setup VNC forwarding
        self.setup_vnc_forwarding()

    def setup_mqtt(self):
        """Setup MQTT client for integration with RPi emulator"""
        try:
            self.mqtt_client = mqtt.Client(client_id="hmi-monitor")
            self.mqtt_client.on_connect = self.on_mqtt_connect
            self.mqtt_client.on_message = self.on_mqtt_message
            
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
            # Subscribe to RPi emulator topics
            client.subscribe("rpi/display/+")
            client.subscribe("rpi/status")
            client.subscribe("rpi/gpio/+")
        else:
            logger.error(f"Failed to connect to MQTT broker: {rc}")

    def on_mqtt_message(self, client, userdata, msg):
        """Handle MQTT messages from RPi emulator"""
        try:
            topic = msg.topic
            payload = json.loads(msg.payload.decode())
            
            if topic.startswith("rpi/display/"):
                self.handle_display_message(topic, payload)
            elif topic == "rpi/status":
                self.handle_status_message(payload)
                
        except Exception as e:
            logger.error(f"Error processing MQTT message: {e}")

    def handle_display_message(self, topic, payload):
        """Handle display-related MQTT messages"""
        if topic == "rpi/display/resolution":
            self.current_resolution = payload
            self.broadcast_to_clients({
                'type': 'resolution_changed',
                'resolution': payload
            })
        elif topic == "rpi/display/refresh_rate":
            self.refresh_rate = payload.get('rate', 60)

    def handle_status_message(self, payload):
        """Handle status messages from RPi"""
        self.broadcast_to_clients({
            'type': 'monitor_status',
            'status': payload
        })

    def setup_vnc_forwarding(self):
        """Setup VNC connection forwarding"""
        threading.Thread(target=self.vnc_connection_manager, daemon=True).start()

    def vnc_connection_manager(self):
        """Manage VNC connection to RPi"""
        while True:
            try:
                if not self.vnc_connected:
                    logger.info("Attempting VNC connection...")
                    # Try to connect to VNC server
                    result = subprocess.run(
                        ['nc', '-z', self.vnc_host, str(self.vnc_port)],
                        capture_output=True,
                        timeout=5
                    )
                    
                    if result.returncode == 0:
                        self.vnc_connected = True
                        logger.info("VNC server is available")
                        self.start_vnc_stream()
                    else:
                        logger.debug("VNC server not available, retrying...")
                
                time.sleep(5)
                
            except Exception as e:
                logger.error(f"VNC connection manager error: {e}")
                time.sleep(10)

    def start_vnc_stream(self):
        """Start VNC streaming to WebSocket clients"""
        threading.Thread(target=self.vnc_frame_capture, daemon=True).start()

    def vnc_frame_capture(self):
        """Capture frames from VNC and stream to clients"""
        try:
            # Use ffmpeg to capture VNC stream and convert to WebSocket-friendly format
            cmd = [
                'ffmpeg',
                '-f', 'x11grab',
                '-video_size', f"{self.current_resolution['width']}x{self.current_resolution['height']}",
                '-framerate', str(self.refresh_rate),
                '-i', f":{self.vnc_port}",
                '-vcodec', 'mjpeg',
                '-q:v', '3',
                '-f', 'image2pipe',
                '-'
            ]
            
            logger.info("Starting VNC frame capture...")
            
            while self.vnc_connected and self.is_powered:
                # For now, generate synthetic frames (placeholder)
                self.generate_synthetic_frame()
                time.sleep(1.0 / self.refresh_rate)
                
        except Exception as e:
            logger.error(f"VNC frame capture error: {e}")
            self.vnc_connected = False

    def generate_synthetic_frame(self):
        """Generate synthetic frame for testing (replace with actual VNC capture)"""
        try:
            # Create a test image
            width, height = self.current_resolution['width'], self.current_resolution['height']
            
            # Scale down for WebSocket transmission
            display_width, display_height = 800, 600
            
            # Create test pattern
            img = Image.new('RGB', (display_width, display_height), color='black')
            draw = ImageDraw.Draw(img)
            
            # Draw test pattern
            timestamp = datetime.now().strftime("%H:%M:%S")
            
            # Grid pattern
            for i in range(0, display_width, 50):
                draw.line([(i, 0), (i, display_height)], fill='#333333', width=1)
            for i in range(0, display_height, 50):
                draw.line([(0, i), (display_width, i)], fill='#333333', width=1)
            
            # Information overlay
            draw.text((20, 20), f"HMI Virtual Monitor", fill='#00d4ff')
            draw.text((20, 50), f"Resolution: {width}x{height}", fill='#ffffff')
            draw.text((20, 80), f"Input: {self.input_source.upper()}", fill='#ffffff')
            draw.text((20, 110), f"Time: {timestamp}", fill='#ffffff')
            draw.text((20, 140), f"Refresh: {self.refresh_rate} Hz", fill='#ffffff')
            
            # Center logo/pattern
            center_x, center_y = display_width // 2, display_height // 2
            draw.ellipse([center_x-50, center_y-50, center_x+50, center_y+50], 
                        outline='#00d4ff', width=3)
            draw.text((center_x-30, center_y-10), "RPi", fill='#00d4ff')
            
            # Convert to bytes for WebSocket transmission
            import io
            img_bytes = io.BytesIO()
            img.save(img_bytes, format='JPEG', quality=85)
            frame_data = img_bytes.getvalue()
            
            # Send to WebSocket clients
            if self.vnc_clients:
                asyncio.create_task(self.broadcast_frame(frame_data))
                
            # Update statistics
            self.frame_stats['frames_sent'] += 1
            
        except Exception as e:
            logger.error(f"Error generating synthetic frame: {e}")

    async def broadcast_frame(self, frame_data):
        """Broadcast frame data to VNC WebSocket clients"""
        if self.vnc_clients:
            disconnected_clients = set()
            for client in self.vnc_clients:
                try:
                    await client.send(frame_data)
                except websockets.exceptions.ConnectionClosed:
                    disconnected_clients.add(client)
                except Exception as e:
                    logger.error(f"Error sending frame to client: {e}")
                    disconnected_clients.add(client)
            
            # Remove disconnected clients
            self.vnc_clients -= disconnected_clients

    async def handle_websocket_client(self, websocket, path):
        """Handle WebSocket client connections"""
        try:
            if path == '/vnc':
                # VNC stream client
                self.vnc_clients.add(websocket)
                logger.info(f"VNC client connected: {websocket.remote_address}")
                
                try:
                    await websocket.wait_closed()
                finally:
                    self.vnc_clients.discard(websocket)
                    logger.info(f"VNC client disconnected: {websocket.remote_address}")
                    
            else:
                # Control client
                self.clients.add(websocket)
                logger.info(f"Control client connected: {websocket.remote_address}")
                
                # Send initial status
                await websocket.send(json.dumps({
                    'type': 'monitor_status',
                    'resolution': self.current_resolution,
                    'refresh_rate': self.refresh_rate,
                    'input_source': self.input_source,
                    'is_powered': self.is_powered,
                    'vnc_connected': self.vnc_connected
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

    async def handle_client_message(self, websocket, message):
        """Handle messages from WebSocket clients"""
        try:
            msg_type = message.get('type')
            
            if msg_type == 'change_resolution':
                await self.change_resolution(message.get('resolution'))
            elif msg_type == 'change_input':
                await self.change_input_source(message.get('source'))
            elif msg_type == 'power_toggle':
                await self.toggle_power()
            elif msg_type == 'start_capture':
                await self.start_capture(message)
            elif msg_type == 'stop_capture':
                await self.stop_capture()
            elif msg_type == 'canvas_click':
                await self.handle_canvas_click(message)
            else:
                logger.warning(f"Unknown message type: {msg_type}")
                
        except Exception as e:
            logger.error(f"Error handling client message: {e}")

    async def change_resolution(self, resolution):
        """Change monitor resolution"""
        self.current_resolution = resolution
        logger.info(f"Resolution changed to: {resolution['width']}x{resolution['height']}")
        
        # Notify RPi emulator via MQTT
        if self.mqtt_client:
            self.mqtt_client.publish("hmi/monitor/resolution", json.dumps(resolution))
        
        # Broadcast to clients
        await self.broadcast_to_clients({
            'type': 'resolution_changed',
            'resolution': resolution
        })

    async def change_input_source(self, source):
        """Change input source"""
        self.input_source = source
        logger.info(f"Input source changed to: {source}")
        
        # Notify via MQTT
        if self.mqtt_client:
            self.mqtt_client.publish("hmi/monitor/input", source)
        
        await self.broadcast_to_clients({
            'type': 'input_switched',
            'source': source
        })

    async def toggle_power(self):
        """Toggle monitor power"""
        self.is_powered = not self.is_powered
        logger.info(f"Monitor power: {'ON' if self.is_powered else 'OFF'}")
        
        await self.broadcast_to_clients({
            'type': 'power_changed',
            'powered': self.is_powered
        })

    async def start_capture(self, message):
        """Start screen capture"""
        self.is_capturing = True
        quality = message.get('quality', 'medium')
        frame_rate = message.get('frameRate', 30)
        
        logger.info(f"Starting capture: quality={quality}, fps={frame_rate}")
        
        # Implementation for actual screen capture would go here
        
        await self.broadcast_to_clients({
            'type': 'capture_started',
            'quality': quality,
            'frame_rate': frame_rate
        })

    async def stop_capture(self):
        """Stop screen capture"""
        self.is_capturing = False
        logger.info("Stopping capture")
        
        await self.broadcast_to_clients({
            'type': 'capture_stopped'
        })

    async def handle_canvas_click(self, message):
        """Handle click on monitor canvas"""
        x, y = message.get('x', 0), message.get('y', 0)
        logger.info(f"Canvas click at: ({x}, {y})")
        
        # Forward click to RPi emulator via MQTT
        if self.mqtt_client:
            self.mqtt_client.publish("hmi/monitor/click", json.dumps({
                'x': x, 'y': y,
                'resolution': self.current_resolution
            }))

    async def broadcast_to_clients(self, message):
        """Broadcast message to all connected clients"""
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

    def update_frame_stats(self):
        """Update frame statistics periodically"""
        while True:
            try:
                # Calculate FPS and other stats
                time.sleep(1)
                # Stats calculation would be more sophisticated in production
                
            except Exception as e:
                logger.error(f"Error updating frame stats: {e}")

def main():
    """Main function to start the virtual monitor backend"""
    logger.info("Starting HMI Virtual Monitor Backend...")
    
    # Create backend instance
    backend = VirtualMonitorBackend()
    
    # Start frame stats updater
    threading.Thread(target=backend.update_frame_stats, daemon=True).start()
    
    # Start WebSocket server
    async def websocket_handler(websocket, path):
        await backend.handle_websocket_client(websocket, path)
    
    # Start servers
    start_server = websockets.serve(websocket_handler, "0.0.0.0", 5558)
    vnc_server = websockets.serve(websocket_handler, "0.0.0.0", 5559)
    
    logger.info("WebSocket servers starting on ports 5558 (control) and 5559 (VNC)")
    
    # Run event loop
    loop = asyncio.get_event_loop()
    loop.run_until_complete(start_server)
    loop.run_until_complete(vnc_server)
    
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        logger.info("Shutting down...")
    finally:
        loop.close()

if __name__ == "__main__":
    main()
