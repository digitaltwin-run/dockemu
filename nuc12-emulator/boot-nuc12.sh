#!/bin/bash

# NUC12 Intel i5 Emulator Boot Script
# Emulates Intel NUC12 with i5 processor using QEMU x86_64

set -e

echo "=== NUC12 Intel i5 Emulator Starting ==="

# Configuration
MACHINE_TYPE="${QEMU_MACHINE:-pc-q35-7.2}"
CPU_TYPE="${QEMU_CPU:-Skylake-Client-v2}"  # Intel i5 equivalent
MEMORY="${QEMU_MEMORY:-4G}"
CORES="${QEMU_CORES:-4}"
THREADS="${QEMU_THREADS:-8}"

# Directories
IMAGES_DIR="/nuc12/images"
SHARED_DIR="/nuc12/shared"
BIOS_DIR="/nuc12/bios"

# Networking
NETWORK_MODEL="e1000"  # Intel NIC emulation
SSH_PORT="2223"
VNC_PORT="5902"

# Find the first .img or .iso file in images directory
IMAGE_FILE=""
for file in "$IMAGES_DIR"/*.img "$IMAGES_DIR"/*.iso; do
    if [ -f "$file" ]; then
        IMAGE_FILE="$file"
        echo "Found image: $IMAGE_FILE"
        break
    fi
done

if [ -z "$IMAGE_FILE" ]; then
    echo "No .img or .iso file found in $IMAGES_DIR"
    echo "Please place a bootable image in the rpi3iso/ directory"
    exit 1
fi

# Check if we need to expand the image
if [[ "$IMAGE_FILE" == *.img ]] && [ $(stat -c%s "$IMAGE_FILE") -lt 8589934592 ]; then
    echo "Expanding image to 8GB for better performance..."
    qemu-img resize "$IMAGE_FILE" 8G
fi

# Start API bridge in background
echo "Starting NUC12 API bridge..."
python3 /nuc12/nuc12-api-bridge.py &
API_PID=$!

# Function to cleanup on exit
cleanup() {
    echo "Shutting down NUC12 emulator..."
    if [ -n "$API_PID" ]; then
        kill $API_PID 2>/dev/null || true
    fi
    exit 0
}
trap cleanup SIGTERM SIGINT

echo "=== NUC12 Configuration ==="
echo "Machine: $MACHINE_TYPE"
echo "CPU: $CPU_TYPE (Intel i5 equivalent)"
echo "Memory: $MEMORY"
echo "Cores: $CORES, Threads: $THREADS"
echo "Image: $IMAGE_FILE"
echo "SSH: localhost:$SSH_PORT"
echo "VNC: localhost:$VNC_PORT"
echo "API: localhost:4002"
echo "=========================="

# Build QEMU command for NUC12 (x86_64)
QEMU_CMD="qemu-system-x86_64"
QEMU_ARGS=""

# Machine and CPU
QEMU_ARGS="$QEMU_ARGS -machine $MACHINE_TYPE -accel tcg"
QEMU_ARGS="$QEMU_ARGS -cpu $CPU_TYPE -smp cores=$CORES,threads=$THREADS"
QEMU_ARGS="$QEMU_ARGS -m $MEMORY"

# UEFI BIOS (for modern Intel systems)
if [ -f "$BIOS_DIR/OVMF_CODE.fd" ]; then
    QEMU_ARGS="$QEMU_ARGS -drive if=pflash,format=raw,readonly=on,file=$BIOS_DIR/OVMF_CODE.fd"
fi

# Storage
QEMU_ARGS="$QEMU_ARGS -drive file=$IMAGE_FILE,format=raw,if=virtio"

# Network with port forwarding for SSH
QEMU_ARGS="$QEMU_ARGS -netdev user,id=net0,hostfwd=tcp::$SSH_PORT-:22"
QEMU_ARGS="$QEMU_ARGS -device $NETWORK_MODEL,netdev=net0"

# Graphics and VNC
QEMU_ARGS="$QEMU_ARGS -vnc :2"  # VNC on port 5902
QEMU_ARGS="$QEMU_ARGS -vga std"

# USB and input
QEMU_ARGS="$QEMU_ARGS -usb -device usb-kbd -device usb-mouse"

# Serial console
QEMU_ARGS="$QEMU_ARGS -serial stdio"

# No GUI (headless)
QEMU_ARGS="$QEMU_ARGS -nographic -daemonize"

echo "Starting QEMU NUC12 emulator..."
echo "Command: $QEMU_CMD $QEMU_ARGS"

# Start QEMU
$QEMU_CMD $QEMU_ARGS

echo "NUC12 emulator started successfully!"
echo "Access via:"
echo "  SSH: ssh -p $SSH_PORT user@localhost"
echo "  VNC: localhost:$VNC_PORT"
echo "  API: http://localhost:4002"

# Wait for API bridge to stay running
wait $API_PID
