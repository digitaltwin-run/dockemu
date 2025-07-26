FROM python:3.9-slim

WORKDIR /app

# Install dependencies for testing and data analysis
RUN pip install pytest numpy pandas flask flask-cors paho-mqtt requests

# Copy application files
COPY . .

EXPOSE 5003

CMD ["python", "bls_tests.py"]