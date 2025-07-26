#!/bin/bash

# Start script for HMI Touchpad service
echo "🎮 Starting HMI Touchpad service..."

# Start nginx in background
nginx -g "daemon off;" &

# Start Python backend if it exists
if [ -f "touchpad-backend.py" ]; then
    echo "📱 Starting touchpad backend..."
    python3 touchpad-backend.py &
fi

# Wait for any process to exit
wait
