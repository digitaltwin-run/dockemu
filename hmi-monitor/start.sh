#!/bin/sh

# HMI Monitor Service Startup Script

echo "Starting HMI Monitor Service..."

# Create necessary directories
mkdir -p /app/captures /app/stream

# Set permissions
chmod 755 /app/captures /app/stream

# Start the Python backend for monitor control and VNC streaming
echo "Starting monitor backend..."
python3 /app/monitor-backend.py &
BACKEND_PID=$!

# Wait for backend to initialize
sleep 3

# Start nginx for web interface
echo "Starting nginx web server..."
nginx -g 'daemon off;' &
NGINX_PID=$!

# Function to handle shutdown
shutdown() {
    echo "Shutting down HMI Monitor Service..."
    kill $BACKEND_PID 2>/dev/null
    kill $NGINX_PID 2>/dev/null
    exit 0
}

# Set up signal handlers
trap shutdown SIGTERM SIGINT

# Wait for processes
wait
