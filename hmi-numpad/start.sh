#!/bin/bash

# HMI Numpad Service Startup Script

echo "Starting HMI Numpad Service..."

# Create necessary directories
mkdir -p /app/logs

# Set permissions
chmod 755 /app/logs

# Start the Python backend for numpad event handling
echo "Starting numpad backend..."
python3 /app/numpad-backend.py &
BACKEND_PID=$!

# Wait for backend to initialize
sleep 2

# Start nginx for web interface
echo "Starting nginx web server..."
nginx -g 'daemon off;' &
NGINX_PID=$!

# Function to handle shutdown
shutdown() {
    echo "Shutting down HMI Numpad Service..."
    kill $BACKEND_PID 2>/dev/null
    kill $NGINX_PID 2>/dev/null
    exit 0
}

# Set up signal handlers
trap shutdown SIGTERM SIGINT

# Wait for processes
wait
