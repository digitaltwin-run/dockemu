#!/bin/bash

set -e

# Configuration
RPI_IMAGE_DIR="/rpi/images"
SHARED_DIR="/rpi/shared"
QEMU_CPU="cortex-a72"
QEMU_MACHINE="raspi3b"
QEMU_MEMORY="1G"
SSH_PORT="2222"
VNC_PORT="5901"
API_PORT="4000"

echo "=== Raspberry Pi OS QEMU Emulator ==="
echo "Starting QEMU-based Raspberry Pi virtualization..."

# Function to find RPi image
find_rpi_image() {
    local image_file=""
    
    # Look for .img files first (preferred)
    for img in "$RPI_IMAGE_DIR"/*.img; do
        if [ -f "$img" ]; then
            image_file="$img"
            echo "Found Raspberry Pi image: $(basename "$img")" >&2
            break
        fi
    done
    
    # If no .img found, look for .iso files
    if [ -z "$image_file" ]; then
        for iso in "$RPI_IMAGE_DIR"/*.iso; do
            if [ -f "$iso" ]; then
                image_file="$iso"
                echo "Found Raspberry Pi ISO: $(basename "$iso")" >&2
                break
            fi
        done
    fi
    
    if [ -z "$image_file" ]; then
        echo "ERROR: No Raspberry Pi image found in $RPI_IMAGE_DIR" >&2
        echo "Please place a .img or .iso file in the images directory" >&2
        exit 1
    fi
    
    echo "$image_file"
}

# Function to prepare image
prepare_image() {
    local source_image="$1"
    local work_image="/rpi/raspios-working.img"
    
    echo "Preparing working image from: $(basename "$source_image")" >&2
    
    # Copy image if it doesn't exist or source is newer
    if [ ! -f "$work_image" ] || [ "$source_image" -nt "$work_image" ]; then
        echo "Creating working copy of image..." >&2
        cp "$source_image" "$work_image"
        
        # Extend image to 8GB for more space
        echo "Extending image to 8GB..." >&2
        qemu-img resize "$work_image" 8G >&2
        
        # Enable SSH by creating ssh file in boot partition
        echo "Enabling SSH..." >&2
        mkdir -p /tmp/rpi-boot
        
        # Mount boot partition (assuming it's the first partition)
        if command -v losetup >/dev/null; then
            # Use loopback device if available
            LOOP_DEVICE=$(losetup -f)
            losetup -P "$LOOP_DEVICE" "$work_image"
            mount "${LOOP_DEVICE}p1" /tmp/rpi-boot 2>/dev/null || true
            touch /tmp/rpi-boot/ssh 2>/dev/null || true
            umount /tmp/rpi-boot 2>/dev/null || true
            losetup -d "$LOOP_DEVICE" 2>/dev/null || true
        fi
        
        rm -rf /tmp/rpi-boot
    fi
    
    echo "$work_image"
}

# Function to start API bridge
start_api_bridge() {
    echo "Starting API bridge on port $API_PORT..."
    python3 /rpi/rpi-api-bridge.py &
    API_PID=$!
    echo "API bridge started with PID: $API_PID"
}

# Function to start QEMU
start_qemu() {
    local image_file="$1"
    
    echo "Starting QEMU with Raspberry Pi OS..."
    echo "SSH will be available on port $SSH_PORT"
    echo "VNC will be available on port $VNC_PORT"
    echo "API bridge available on port $API_PORT"
    
    # QEMU command for Raspberry Pi 3B+
    exec qemu-system-aarch64 \
        -M "$QEMU_MACHINE" \
        -cpu "$QEMU_CPU" \
        -m "$QEMU_MEMORY" \
        -smp 4 \
        -drive "file=$image_file,format=raw,if=sd" \
        -netdev user,id=net0,hostfwd=tcp::${SSH_PORT}-:22 \
        -device usb-net,netdev=net0 \
        -vnc ":1" \
        -serial stdio \
        -no-reboot \
        -monitor unix:/tmp/qemu-monitor,server,nowait
}

# Function to cleanup on exit
cleanup() {
    echo "Cleaning up..."
    if [ ! -z "$API_PID" ]; then
        kill "$API_PID" 2>/dev/null || true
    fi
    
    # Stop QEMU if running
    if [ -S /tmp/qemu-monitor ]; then
        echo "quit" | socat - unix:/tmp/qemu-monitor 2>/dev/null || true
    fi
}

# Set trap for cleanup
trap cleanup EXIT INT TERM

# Main execution
main() {
    echo "Checking for Raspberry Pi images..."
    
    # Find RPi image
    RPI_IMAGE=$(find_rpi_image)
    
    # Prepare working image
    WORK_IMAGE=$(prepare_image "$RPI_IMAGE")
    
    # Start API bridge
    start_api_bridge
    
    # Wait a moment for API bridge to start
    sleep 2
    
    # Start QEMU
    echo "Starting QEMU virtualization..."
    start_qemu "$WORK_IMAGE"
}

# Check if running in container
if [ ! -d "$RPI_IMAGE_DIR" ]; then
    echo "ERROR: Image directory $RPI_IMAGE_DIR not found"
    echo "Make sure to mount the rpi3iso directory to $RPI_IMAGE_DIR"
    exit 1
fi

# Run main function
main
