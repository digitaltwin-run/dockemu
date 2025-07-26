FROM python:3.9-slim

WORKDIR /app

# Install dependencies for I2C and sensor simulation
RUN pip install smbus2 numpy flask flask-cors paho-mqtt

# Copy application files
COPY . .

EXPOSE 5001

CMD ["python", "sensors.py"]