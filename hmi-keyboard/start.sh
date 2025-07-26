#!/bin/bash

set -e

echo "=== HMI Virtual Keyboard ==="
echo "Starting HMI Keyboard service..."

# Start Python backend for keyboard event handling
echo "Starting keyboard event handler..."
python3 /app/keyboard-backend.py &
BACKEND_PID=$!

# Function to cleanup on exit
cleanup() {
    echo "Cleaning up..."
    if [ ! -z "$BACKEND_PID" ]; then
        kill "$BACKEND_PID" 2>/dev/null || true
    fi
    exit 0
}

# Set trap for cleanup
trap cleanup EXIT INT TERM

# Wait a moment for backend to start
sleep 2

# Start nginx
echo "Starting nginx..."
echo "HMI Virtual Keyboard available on port 80"
echo "Keyboard API available on port 5556"

# Start nginx in foreground
exec nginx -g "daemon off;"
