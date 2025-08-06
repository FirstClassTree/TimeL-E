# Use a pre-built base image with common scientific Python packages
FROM python:3.11.9-slim as base

# Set environment variables for optimization
ENV PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive

# Install system dependencies in one optimized layer
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libffi-dev \
    libssl-dev \
    libpq-dev \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create non-root user
RUN adduser --disabled-password --gecos '' --uid 1000 dbservice

# Dependency installation stage
FROM base as deps

WORKDIR /app

# Copy and install Python dependencies (this layer will be cached)
COPY requirements.txt .
RUN pip install --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt && \
    pip list

# Production stage
FROM base as production

WORKDIR /app

# Copy installed packages from deps stage
COPY --from=deps /usr/local/lib/python3.11/site-packages/ /usr/local/lib/python3.11/site-packages/
COPY --from=deps /usr/local/bin/ /usr/local/bin/

# Remove build dependencies to reduce image size
RUN apt-get update && apt-get remove -y --purge \
    build-essential \
    gcc \
    libffi-dev \
    libssl-dev \
    && apt-get autoremove -y \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy application code with proper ownership
COPY --chown=dbservice:dbservice app/ ./app/

# Switch to non-root user
USER dbservice

# Expose default port
EXPOSE 7000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=120s --retries=5 \
    CMD curl -f http://localhost:${DB_SERVICE_PORT}/health || exit 1

# Run application
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${DB_SERVICE_PORT}"]
