FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt

COPY app/ ./app/
COPY data/ ./data/

#CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "7000"]
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${DB_SERVICE_PORT}"]
