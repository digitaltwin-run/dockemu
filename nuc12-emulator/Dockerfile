FROM debian:bullseye-slim

# Install QEMU for x86_64 emulation (Intel i5)
RUN apt-get update && apt-get install -y \
    qemu-system-x86 \
    qemu-utils \
    qemu-kvm \
    wget \
    unzip \
    openssh-client \
    tigervnc-viewer \
    socat \
    python3 \
    python3-pip \
    python3-flask \
    python3-flask-cors \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
RUN pip3 install websockets paho-mqtt

# Create working directories
WORKDIR /nuc12
RUN mkdir -p /nuc12/images /nuc12/shared /nuc12/bios

# Copy emulator scripts and configurations
COPY boot-nuc12.sh /nuc12/
COPY nuc12-api-bridge.py /nuc12/

# Download UEFI BIOS for x86_64 if needed
RUN wget -O /nuc12/bios/OVMF_CODE.fd \
    https://github.com/tianocore/edk2/releases/download/edk2-stable202211/OVMF_CODE.fd || \
    echo "BIOS download failed - will use system default"

# Make scripts executable
RUN chmod +x /nuc12/boot-nuc12.sh

# Expose ports
# 2223 - SSH to NUC12 OS
# 5902 - VNC display  
# 4002 - API bridge
# 8082 - Web management interface
EXPOSE 2223 5902 4002 8082

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:4002/health || exit 1

# Start QEMU with NUC12 emulation
CMD ["/nuc12/boot-nuc12.sh"]
