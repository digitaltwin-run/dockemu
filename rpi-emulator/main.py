#!/usr/bin/env python3
"""
Main entry point for RPi emulator.
Initializes GPIO and I2C simulators and provides API endpoints.
"""

import asyncio
import os
import sys
from flask import Flask, jsonify, request
from flask_cors import CORS

# Import our hardware simulators
from hardware.gpio_controller import GPIOSimulator, GPIOMode
from hardware.i2c_bus import I2CBusSimulator

# Create Flask app
app = Flask(__name__)
CORS(app)

# Global simulator instances
gpio_sim = GPIOSimulator()
i2c_sim = I2CBusSimulator()

@app.route('/api/status', methods=['GET'])
def get_status():
    """Get emulator status."""
    return jsonify({
        'status': 'running',
        'emulation_mode': os.getenv('EMULATION_MODE', 'false') == 'true',
        'gpio_mock': os.getenv('GPIO_MOCK', 'false') == 'true',
        'i2c_mock': os.getenv('I2C_MOCK', 'false') == 'true'
    })

@app.route('/api/gpio/<int:pin>', methods=['GET', 'POST'])
def handle_gpio(pin):
    """Handle GPIO pin operations."""
    if request.method == 'POST':
        data = request.get_json()
        if 'value' in data:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(gpio_sim.write(pin, int(data['value'])))
            loop.close()
    
    # Get current value
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    value = loop.run_until_complete(gpio_sim.read(pin))
    loop.close()
    
    return jsonify({'pin': pin, 'value': value})

@app.route('/api/i2c/<int:address>', methods=['GET', 'POST'])
def handle_i2c(address):
    """Handle I2C device operations."""
    if request.method == 'POST':
        data = request.get_json()
        if 'data' in data:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(i2c_sim.write(address, bytes(data['data'])))
            loop.close()
            return jsonify({'address': address, 'success': result})
    
    # Read from device
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    data = loop.run_until_complete(i2c_sim.read(address, 2))
    loop.close()
    
    return jsonify({'address': address, 'data': list(data)})

def initialize_simulators():
    """Initialize the hardware simulators."""
    print("Initializing RPi emulator...")
    print(f"Emulation mode: {os.getenv('EMULATION_MODE', 'false')}")
    print(f"GPIO mock: {os.getenv('GPIO_MOCK', 'false')}")
    print(f"I2C mock: {os.getenv('I2C_MOCK', 'false')}")
    
    # Setup some default GPIO pins
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    # Setup common pins
    for pin in [18, 19, 20, 21]:  # Common GPIO pins
        loop.run_until_complete(gpio_sim.setup(pin, GPIOMode.OUTPUT))
    
    loop.close()
    print("RPi emulator initialized successfully")

if __name__ == '__main__':
    initialize_simulators()
    
    # Run Flask app
    port = int(os.getenv('PORT', 4000))
    host = os.getenv('HOST', '0.0.0.0')
    
    print(f"Starting RPi emulator on {host}:{port}")
    app.run(host=host, port=port, debug=False)
