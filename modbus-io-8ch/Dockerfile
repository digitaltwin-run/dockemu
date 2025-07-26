FROM python:3.9-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    LOG_LEVEL=INFO

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p /var/log/modbus-io-8ch /var/run/modbus-io-8ch \
    && chmod 755 /var/log/modbus-io-8ch /var/run/modbus-io-8ch

# Make init script executable
RUN chmod +x /app/init.sh

# Expose ports
EXPOSE 5020 8020

# Run the application
CMD ["./init.sh"]
