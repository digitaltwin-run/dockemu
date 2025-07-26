#!/bin/bash

# Create required directories
mkdir -p /var/log/modbus-io-8ch
mkdir -p /var/run/modbus-io-8ch

# Set proper permissions
chown -R nobody:nogroup /var/log/modbus-io-8ch
chown -R nobody:nogroup /var/run/modbus-io-8ch
chmod 755 /var/log/modbus-io-8ch
chmod 755 /var/run/modbus-io-8ch

# Start the application
exec python modbus_io_simulator.py
