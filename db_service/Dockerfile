FROM python:3.11-slim

WORKDIR /app

# Install build dependencies for pip install (critical for slim)
RUN apt-get update && apt-get install -y \
    gcc \
    libffi-dev \
    libssl-dev \
    libpq-dev \
    build-essential \
    curl

# RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

# Install pip requirements
RUN pip install --upgrade pip setuptools wheel \
    && pip install --no-cache-dir -r requirements.txt

# Remove build dependencies after pip install (keep image smaller)
RUN apt-get remove -y build-essential gcc \
    && rm -rf /var/lib/apt/lists/*

COPY app/ ./app/

RUN find /app -name '*.pyc' -delete && find /app -name '__pycache__' -type d -exec rm -rf {} +

# Create a non-root user and set permissions
RUN adduser --disabled-password --gecos '' dbservice && \
    chown -R dbservice /app

USER dbservice

#Expose default port
EXPOSE 7000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:${DB_SERVICE_PORT}/health || exit 1

#CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "7000"]
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${DB_SERVICE_PORT}"]
