# Shared Base Image for nginx + Python HMI Services
# Used by: frontend, hmi-monitor, hmi-numpad, hmi-keyboard, hmi-pad, modbus-visualizer, lcd-display
FROM nginx:alpine

LABEL maintainer="C20 Simulator Team"
LABEL description="Base image for nginx + Python HMI services"
LABEL version="1.0"

# Install common Python packages
RUN apk add --no-cache \
    python3 \
    py3-pip \
    py3-flask \
    py3-flask-cors \
    py3-websockets

# Install common Python dependencies with --break-system-packages
RUN pip3 install --break-system-packages \
    paho-mqtt \
    websockets \
    flask \
    flask-cors

# Create common app directory
WORKDIR /app

# Copy common nginx configuration template
COPY shared/nginx/nginx-base.conf /etc/nginx/nginx.conf

# Create common directories
RUN mkdir -p /app/static /app/templates /app/js /app/css

# Set executable permissions for start scripts
RUN chmod +x /start.sh 2>/dev/null || true

# Common environment variables
ENV FLASK_APP=app.py
ENV FLASK_ENV=production
ENV PYTHONPATH=/app

# Expose standard ports
EXPOSE 80 5555

# Health check template (services can override)
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost/health || exit 1

# Default command (services should override)
CMD ["/start.sh"]
