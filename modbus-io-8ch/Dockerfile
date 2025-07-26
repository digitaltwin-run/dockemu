FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY modbus_io_simulator.py .
COPY web_interface.py .

EXPOSE 5020 8083

CMD ["python", "modbus_io_simulator.py"]
