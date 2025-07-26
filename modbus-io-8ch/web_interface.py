import logging
import threading
from typing import Dict, List, Union, Any

from flask import Blueprint, Flask, jsonify, request
from flask_cors import CORS

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Thread lock for simulator access
simulator_lock = threading.Lock()

# Global reference to simulator (will be set from main module)
simulator = None

def set_simulator(sim):
    """Set the simulator instance for the web interface."""
    global simulator
    simulator = sim

def create_web_blueprint():
    """Create and return the Flask Blueprint with all routes."""
    web_app = Blueprint('web_interface', __name__)
    
    @web_app.route('/api/registers', methods=['GET'])
    def get_registers() -> Dict[str, List[Union[bool, int]]]:
        """Get all register values from the simulator.
        
        Returns:
            JSON response with all register values
        """
        with simulator_lock:
            return jsonify({
                'coils': simulator.digital_outputs,
                'holding_registers': [int(x) for x in simulator.analog_outputs],
                'input_status': simulator.digital_inputs,
                'input_registers': [int(x) for x in simulator.analog_inputs]
            })

    @web_app.route('/api/coils/<int:address>', methods=['GET', 'POST'])
    def handle_coil(address: int) -> Dict[str, Any]:
        """Handle single coil (digital output).
        
        Args:
            address: The coil address (0-7)
        
        Returns:
            JSON response with the coil status or error message
        """
        if address < 0 or address >= 8:
            return jsonify({'error': 'Address out of range'}), 400
        
        if request.method == 'POST':
            data = request.get_json()
            if 'value' not in data:
                return jsonify({'error': 'Missing value'}), 400
                
            with simulator_lock:
                simulator.digital_outputs[address] = bool(data['value'])
                logger.info(f"Set coil {address} to {simulator.digital_outputs[address]}")
        
        with simulator_lock:
            return jsonify({
                'address': address, 
                'value': simulator.digital_outputs[address]
            })

    @web_app.route('/api/holding_register/<int:address>', methods=['GET', 'POST'])
    def handle_holding_register(address: int) -> Dict[str, Any]:
        """Handle holding register (analog output).
        
        Args:
            address: The register address (0-7)
        
        Returns:
            JSON response with the register value or error message
        """
        if address < 0 or address >= 8:
            return jsonify({'error': 'Address out of range'}), 400
        
        if request.method == 'POST':
            data = request.get_json()
            if 'value' not in data or not isinstance(data['value'], int):
                return jsonify({'error': 'Invalid value'}), 400
                
            with simulator_lock:
                simulator.analog_outputs[address] = int(data['value'])
                logger.info(
                    f"Set holding register {address} to "
                    f"{simulator.analog_outputs[address]}"
                )
        
        with simulator_lock:
            return jsonify({
                'address': address, 
                'value': simulator.analog_outputs[address]
            })

    return web_app

def create_web_app():
    """Create standalone Flask app for testing."""
    app = Flask(__name__)
    CORS(app)
    
    # Register blueprint
    blueprint = create_web_blueprint()
    app.register_blueprint(blueprint, url_prefix='/api')
    
    return app

def run_web_interface(host: str = '0.0.0.0', port: int = 8020) -> None:
    """Run the Flask web interface.
    
    Args:
        host: The host to bind to
        port: The port to listen on
    """
    app = create_web_app()
    logger.info(f"Starting web interface on http://{host}:{port}")
    app.run(host=host, port=port, debug=False, use_reloader=False)

if __name__ == '__main__':
    # This allows running the web interface directly for testing
    run_web_interface()
