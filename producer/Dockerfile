FROM python:3.9-slim

WORKDIR /app

RUN apt-get update && apt-get install -y netcat-openbsd && rm -rf /var/lib/apt/lists/*

COPY requirements_producer.txt .
RUN pip install --no-cache-dir -r requirements_producer.txt

COPY producer.py .

CMD ["sh", "-c", "while ! nc -z redpanda 9092; do echo 'Waiting for Redpanda...'; sleep 1; done; echo 'Redpanda is ready!'; python producer.py"]