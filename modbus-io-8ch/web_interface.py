from flask import Blueprint, jsonify, request
import logging
from typing import Dict, List, Union, Any

# Create a Blueprint for the web interface
web_app = Blueprint('web_interface', __name__)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import the simulator instance from the main module
from modbus_io_simulator import simulator

# Lock for thread safety
from threading import Lock
lock = Lock()

@web_app.route('/api/registers', methods=['GET'])
def get_registers() -> Dict[str, List[Union[bool, int]]]:
    """Get all register values from the simulator.
    
    Returns:
        JSON response with all register values
    """
    with lock:
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
            
        with lock:
            simulator.digital_outputs[address] = bool(data['value'])
            logger.info(f"Set coil {address} to {simulator.digital_outputs[address]}")
    
    with lock:
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
            
        with lock:
            simulator.analog_outputs[address] = int(data['value'])
            logger.info(
                f"Set holding register {address} to "
                f"{simulator.analog_outputs[address]}"
            )
    
    with lock:
        return jsonify({
            'address': address, 
            'value': simulator.analog_outputs[address]
        })

def create_web_app() -> 'Flask':
    """Create and configure the Flask application.
    
    Returns:
        Configured Flask application instance
    """
    from flask import Flask
    from flask_cors import CORS
    
    app = Flask(__name__)
    CORS(app)
    app.register_blueprint(web_app, url_prefix='/api')
    
    return app


def run_web_interface(host: str = '0.0.0.0', port: int = 8083) -> None:
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
