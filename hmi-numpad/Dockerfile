FROM nginx:alpine

# Install tools for numpad backend
RUN apk add --no-cache \
    python3 \
    py3-pip \
    py3-flask \
    py3-flask-cors \
    py3-websockets

# Install Python dependencies
RUN pip3 install --break-system-packages paho-mqtt websockets

# Create app directory
WORKDIR /app

# Copy application files
COPY . /app/

# Copy nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Create startup script
COPY start.sh /start.sh
RUN chmod +x /start.sh

EXPOSE 80 5560

CMD ["/start.sh"]
