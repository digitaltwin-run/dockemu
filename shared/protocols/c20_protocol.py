"""
C20 Hardware Protocol Implementation
Defines communication protocols and data structures for C20 system components
"""

import json
import time
from enum import Enum
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Any, Union
import struct

class MessageType(Enum):
    """C20 Protocol Message Types"""
    SYSTEM_STATUS = 0x01
    SENSOR_DATA = 0x02
    VALVE_CONTROL = 0x03
    LCD_DISPLAY = 0x04
    KEYBOARD_INPUT = 0x05
    TEST_PROCEDURE = 0x06
    ALARM = 0x07
    HEARTBEAT = 0x08
    CONFIG_UPDATE = 0x09
    MODBUS_DATA = 0x0A

class DeviceType(Enum):
    """C20 Device Types"""
    RPI_CONTROLLER = "rpi"
    LCD_DISPLAY = "lcd"
    HUI_KEYBOARD = "keyboard"
    PRESSURE_SENSOR = "sensor"
    VALVE_CONTROLLER = "valve"
    MODBUS_IO = "modbus"
    TEST_UNIT = "test"

class SensorType(Enum):
    """Pressure Sensor Types"""
    LOW_PRESSURE = "LP"    # 0-50 mbar
    MEDIUM_PRESSURE = "MP" # 0-200 mbar  
    HIGH_PRESSURE = "HP"   # 0-500 mbar

@dataclass
class C20Message:
    """Base C20 Protocol Message"""
    timestamp: float
    message_type: MessageType
    source_device: DeviceType
    target_device: Optional[DeviceType]
    sequence_id: int
    payload: Dict[str, Any]
    checksum: Optional[str] = None

    def to_json(self) -> str:
        """Convert message to JSON string"""
        data = asdict(self)
        data['message_type'] = self.message_type.value
        data['source_device'] = self.source_device.value
        data['target_device'] = self.target_device.value if self.target_device else None
        return json.dumps(data)

    @classmethod
    def from_json(cls, json_str: str) -> 'C20Message':
        """Create message from JSON string"""
        data = json.loads(json_str)
        return cls(
            timestamp=data['timestamp'],
            message_type=MessageType(data['message_type']),
            source_device=DeviceType(data['source_device']),
            target_device=DeviceType(data['target_device']) if data['target_device'] else None,
            sequence_id=data['sequence_id'],
            payload=data['payload'],
            checksum=data.get('checksum')
        )

@dataclass
class SensorData:
    """Pressure Sensor Data Structure"""
    sensor_type: SensorType
    i2c_address: int
    pressure_mbar: float
    temperature_c: float
    voltage_v: float
    status: str  # "OK", "WARNING", "ERROR"
    calibration_date: str
    serial_number: str

@dataclass  
class ValveState:
    """Valve Controller State"""
    valve_id: int
    i2c_address: int
    output_state: bool  # True = Open, False = Closed
    pwm_duty_cycle: float  # 0.0 - 1.0
    current_ma: float
    status: str  # "OK", "WARNING", "ERROR"

@dataclass
class SystemStatus:
    """Overall System Status"""
    system_mode: str  # "STANDBY", "TESTING", "ALARM", "MAINTENANCE"
    cpu_usage: float
    memory_usage: float
    temperature: float
    uptime_seconds: int
    active_alarms: List[str]
    connected_devices: List[DeviceType]

@dataclass
class TestProcedure:
    """Test Procedure Definition"""
    procedure_id: str
    name: str
    description: str
    steps: List[Dict[str, Any]]
    expected_duration_s: int
    required_devices: List[DeviceType]
    parameters: Dict[str, Any]

class C20Protocol:
    """C20 Communication Protocol Handler"""
    
    def __init__(self, device_type: DeviceType):
        self.device_type = device_type
        self.sequence_counter = 0
        self.message_handlers = {}
        self.setup_default_handlers()

    def setup_default_handlers(self):
        """Setup default message handlers"""
        self.message_handlers[MessageType.HEARTBEAT] = self.handle_heartbeat
        self.message_handlers[MessageType.SYSTEM_STATUS] = self.handle_system_status
        self.message_handlers[MessageType.ALARM] = self.handle_alarm

    def create_message(
        self, 
        message_type: MessageType, 
        payload: Dict[str, Any],
        target_device: Optional[DeviceType] = None
    ) -> C20Message:
        """Create a new protocol message"""
        self.sequence_counter += 1
        
        message = C20Message(
            timestamp=time.time(),
            message_type=message_type,
            source_device=self.device_type,
            target_device=target_device,
            sequence_id=self.sequence_counter,
            payload=payload
        )
        
        # Calculate checksum
        message.checksum = self.calculate_checksum(message)
        return message

    def calculate_checksum(self, message: C20Message) -> str:
        """Calculate message checksum for integrity verification"""
        data = f"{message.timestamp}{message.message_type.value}{message.sequence_id}{json.dumps(message.payload, sort_keys=True)}"
        return hex(hash(data) & 0xFFFFFFFF)[2:]

    def verify_checksum(self, message: C20Message) -> bool:
        """Verify message checksum"""
        expected = self.calculate_checksum(message)
        return expected == message.checksum

    def process_message(self, message: C20Message) -> Optional[C20Message]:
        """Process incoming message and return response if needed"""
        if not self.verify_checksum(message):
            return self.create_error_response(message, "CHECKSUM_ERROR")
        
        handler = self.message_handlers.get(message.message_type)
        if handler:
            return handler(message)
        else:
            return self.create_error_response(message, "UNKNOWN_MESSAGE_TYPE")

    def handle_heartbeat(self, message: C20Message) -> C20Message:
        """Handle heartbeat message"""
        return self.create_message(
            MessageType.HEARTBEAT,
            {
                "status": "alive",
                "device_type": self.device_type.value,
                "timestamp": time.time()
            },
            message.source_device
        )

    def handle_system_status(self, message: C20Message) -> Optional[C20Message]:
        """Handle system status request"""
        # This would be implemented by each device type
        return None

    def handle_alarm(self, message: C20Message) -> Optional[C20Message]:
        """Handle alarm message"""
        print(f"ALARM: {message.payload}")
        return None

    def create_error_response(self, original_message: C20Message, error_code: str) -> C20Message:
        """Create error response message"""
        return self.create_message(
            MessageType.ALARM,
            {
                "error_code": error_code,
                "original_sequence": original_message.sequence_id,
                "original_type": original_message.message_type.value
            },
            original_message.source_device
        )

    def create_sensor_data_message(self, sensor_data: SensorData) -> C20Message:
        """Create sensor data message"""
        return self.create_message(
            MessageType.SENSOR_DATA,
            {
                "sensor_type": sensor_data.sensor_type.value,
                "i2c_address": sensor_data.i2c_address,
                "pressure_mbar": sensor_data.pressure_mbar,
                "temperature_c": sensor_data.temperature_c,
                "voltage_v": sensor_data.voltage_v,
                "status": sensor_data.status,
                "calibration_date": sensor_data.calibration_date,
                "serial_number": sensor_data.serial_number
            }
        )

    def create_valve_control_message(self, valve_states: List[ValveState]) -> C20Message:
        """Create valve control message"""
        return self.create_message(
            MessageType.VALVE_CONTROL,
            {
                "valves": [
                    {
                        "valve_id": v.valve_id,
                        "i2c_address": v.i2c_address,
                        "output_state": v.output_state,
                        "pwm_duty_cycle": v.pwm_duty_cycle,
                        "current_ma": v.current_ma,
                        "status": v.status
                    } for v in valve_states
                ]
            }
        )

    def create_lcd_display_message(self, display_data: Dict[str, Any]) -> C20Message:
        """Create LCD display message"""
        return self.create_message(
            MessageType.LCD_DISPLAY,
            display_data,
            DeviceType.LCD_DISPLAY
        )

    def create_keyboard_input_message(self, key_data: Dict[str, Any]) -> C20Message:
        """Create keyboard input message"""
        return self.create_message(
            MessageType.KEYBOARD_INPUT,
            key_data
        )

    def create_test_procedure_message(self, procedure: TestProcedure, action: str) -> C20Message:
        """Create test procedure message"""
        return self.create_message(
            MessageType.TEST_PROCEDURE,
            {
                "action": action,  # "START", "STOP", "PAUSE", "RESUME", "STATUS"
                "procedure_id": procedure.procedure_id,
                "name": procedure.name,
                "description": procedure.description,
                "steps": procedure.steps,
                "expected_duration_s": procedure.expected_duration_s,
                "required_devices": [d.value for d in procedure.required_devices],
                "parameters": procedure.parameters
            }
        )

    def create_modbus_data_message(self, modbus_data: Dict[str, Any]) -> C20Message:
        """Create Modbus data message"""
        return self.create_message(
            MessageType.MODBUS_DATA,
            modbus_data
        )

# Protocol Constants
class ProtocolConstants:
    """C20 Protocol Constants"""
    
    # I2C Addresses
    I2C_ADDRESSES = {
        "HUI_KEYBOARD": 0x20,
        "VALVE_CONTROLLER": 0x21,
        "SENSOR_LP": 0x48,
        "SENSOR_MP": 0x49,
        "SENSOR_HP": 0x4A
    }
    
    # Communication Ports
    PORTS = {
        "MQTT": 1883,
        "WEBSOCKET": 9001,
        "LCD_DISPLAY": 8081,
        "HUI_KEYBOARD": 8082,
        "MODBUS_API": 8083,
        "MODBUS_VIZ": 8084,
        "MAIN_GUI": 8088
    }
    
    # Sensor Ranges (mbar)
    SENSOR_RANGES = {
        SensorType.LOW_PRESSURE: (0, 50),
        SensorType.MEDIUM_PRESSURE: (0, 200),
        SensorType.HIGH_PRESSURE: (0, 500)
    }
    
    # System Modes
    SYSTEM_MODES = [
        "STANDBY",
        "TESTING", 
        "ALARM",
        "MAINTENANCE",
        "CALIBRATION"
    ]
    
    # Standard Test Procedures
    TEST_PROCEDURES = {
        "BLS_5000_TEST": "BLS 5000 Mask Leak Test",
        "BLS_8000_TEST": "BLS 8000 Mask Leak Test", 
        "VALVE_CALIBRATION": "Valve Response Calibration",
        "SENSOR_CALIBRATION": "Pressure Sensor Calibration",
        "SYSTEM_SELFTEST": "Complete System Self-Test"
    }

# Utility Functions
def create_default_system_status() -> SystemStatus:
    """Create default system status"""
    return SystemStatus(
        system_mode="STANDBY",
        cpu_usage=0.0,
        memory_usage=0.0,
        temperature=25.0,
        uptime_seconds=0,
        active_alarms=[],
        connected_devices=[DeviceType.RPI_CONTROLLER]
    )

def create_test_sensor_data(sensor_type: SensorType, address: int) -> SensorData:
    """Create test sensor data"""
    import random
    
    ranges = ProtocolConstants.SENSOR_RANGES[sensor_type]
    pressure = random.uniform(ranges[0], ranges[1])
    
    return SensorData(
        sensor_type=sensor_type,
        i2c_address=address,
        pressure_mbar=pressure,
        temperature_c=random.uniform(20, 30),
        voltage_v=random.uniform(4.8, 5.2),
        status="OK",
        calibration_date="2024-01-01",
        serial_number=f"SN{sensor_type.value}{address:02X}"
    )

def create_test_valve_state(valve_id: int, address: int) -> ValveState:
    """Create test valve state"""
    import random
    
    return ValveState(
        valve_id=valve_id,
        i2c_address=address,
        output_state=random.choice([True, False]),
        pwm_duty_cycle=random.uniform(0.0, 1.0),
        current_ma=random.uniform(10, 50),
        status="OK"
    )