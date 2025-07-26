FROM python:3.9-slim

WORKDIR /app

# Install dependencies
RUN pip install flask flask-cors websocket-client

# Copy application files
COPY . .

EXPOSE 80

CMD ["python", "server.py"]