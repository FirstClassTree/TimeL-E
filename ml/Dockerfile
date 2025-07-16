# ml-service/Dockerfile - ENHANCED for Production-Ready ML Service

# ============================================================================
# BUILD STAGE - Compile dependencies and prepare environment
# ============================================================================
FROM python:3.9-slim as builder

# Set working directory
WORKDIR /app

# Install system dependencies for building Python packages
RUN apt-get update && apt-get install -y \
    build-essential \
    gcc \
    g++ \
    libpq-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better Docker layer caching
COPY requirements.txt .

# Create virtual environment and install dependencies
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Upgrade pip and install dependencies
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# ============================================================================
# PRODUCTION STAGE - Minimal runtime environment
# ============================================================================
FROM python:3.9-slim as production

# Set working directory
WORKDIR /app

# Install only runtime dependencies
RUN apt-get update && apt-get install -y \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copy virtual environment from builder stage
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Create non-root user for security
RUN groupadd -r mluser && useradd -r -g mluser mluser

# Create necessary directories with proper permissions
RUN mkdir -p /app/models /app/training-data /app/logs && \
    chown -R mluser:mluser /app

# Copy application code
COPY --chown=mluser:mluser src/ ./src/
COPY --chown=mluser:mluser *.py ./

# Set Python path and other environment variables
ENV PYTHONPATH=/app \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONIOENCODING=utf-8

# Health check script
COPY --chown=mluser:mluser <<EOF /app/healthcheck.py
#!/usr/bin/env python3
import sys
import requests
try:
    response = requests.get('http://localhost:8000/health', timeout=10)
    if response.status_code == 200 and response.json().get('status') == 'healthy':
        sys.exit(0)
    else:
        sys.exit(1)
except:
    sys.exit(1)
EOF

RUN chmod +x /app/healthcheck.py

# Switch to non-root user
USER mluser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD python /app/healthcheck.py

# Start command with proper signal handling
CMD ["python", "-m", "uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]

# ============================================================================
# PRODUCTION OPTIMIZATIONS:
# 
# 1. Multi-stage build for smaller final image
# 2. Non-root user for security
# 3. Minimal runtime dependencies
# 4. Proper Python environment configuration
# 5. Health check with proper timeout
# 6. Signal handling for graceful shutdown
# 7. Clean apt cache to reduce image size
# 8. Virtual environment isolation
# 9. Proper file permissions
# 10. Single worker for predictable resource usage
# ============================================================================