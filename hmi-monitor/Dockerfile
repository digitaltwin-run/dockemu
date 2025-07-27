FROM php:8.2-fpm-alpine

# Install Caddy and tools for virtual monitor/display
RUN apk add --no-cache \
    caddy \
    python3 \
    py3-pip \
    py3-flask \
    py3-flask-cors \
    py3-websockets \
    py3-pillow \
    ffmpeg \
    supervisor

# Install Python dependencies
RUN pip3 install --break-system-packages paho-mqtt websockets flask flask-cors

# Create app directory
WORKDIR /app

# Copy application files
COPY . /app/

# Copy Caddy configuration
COPY Caddyfile /etc/caddy/Caddyfile

# Create startup script
COPY start.sh /start.sh
RUN chmod +x /start.sh

# Create directories for screen capture and streaming
RUN mkdir -p /app/captures /app/stream

EXPOSE 80 5558 5559

CMD ["/start.sh"]
