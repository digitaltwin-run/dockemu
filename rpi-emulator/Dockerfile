FROM python:3.9-slim

RUN apt-get update && apt-get install -y \
    python3-smbus \
    i2c-tools \
    python3-dev \
    python3-pip \
    netcat-openbsd \
    socat

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["python", "boot.sh"]