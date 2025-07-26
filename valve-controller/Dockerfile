FROM python:3.9-slim

WORKDIR /app

# Install dependencies for I2C and valve control
RUN pip install smbus2 flask flask-cors paho-mqtt numpy

# Copy application files
COPY . .

EXPOSE 5002

CMD ["python", "pcb_out_12.py"]