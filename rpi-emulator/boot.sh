#!/bin/bash

# Start the main emulator service
python -m hardware.modbus_simulator &

# Keep the container running
tail -f /dev/null
