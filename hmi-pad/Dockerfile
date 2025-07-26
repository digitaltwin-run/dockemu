FROM nginx:alpine

# Install basic tools for touch/gesture emulation
RUN apk add --no-cache \
    python3 \
    py3-pip \
    py3-flask \
    py3-flask-cors

# Create app directory
WORKDIR /app

# Copy application files
COPY . /app/

# Copy nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Create startup script
COPY start.sh /start.sh
RUN chmod +x /start.sh

EXPOSE 80 5555

CMD ["/start.sh"]
