# ml-service/Dockerfile - ENHANCED for Production-Ready ML Service

# ============================================================================
# BUILD STAGE - Compile dependencies and prepare environment
# ============================================================================
FROM python:3.9-slim as builder
#FROM python:3.9-bullseye as builder
#FROM python:3.11-bullseye as builder
#FROM python:3.10.14-slim as builder

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

ENV PIP_NO_CACHE_DIR=1

# Upgrade pip + wheels
RUN pip install --upgrade pip setuptools wheel

# Force upgrade pip
RUN pip install --upgrade pip==25.1.1

# Install dependencies ONE BY ONE for low memory
#RUN grep -vE '^\s*#|^\s*$' requirements.txt | xargs -n 1 pip install
#RUN grep -vE '^\s*#|^\s*$' requirements.txt | xargs -n 1 -I {} sh -c 'echo "Installing {}" && pip install --no-cache-dir "{}"'
RUN pip -v install fastapi==0.103.1
RUN pip -v install uvicorn==0.23.2
RUN pip -v install pydantic==2.3.0
#RUN pip -v install --upgrade numpy pandas
RUN pip -v install numpy==1.24.3
RUN pip -v install pandas==2.0.3
#RUN pip -v install pandas==2.2.3
#RUN pip -v install scipy==1.11.2
RUN pip -v install scipy==1.13.0
RUN pip -v install lightgbm==4.0.0
RUN pip -v install sqlalchemy==2.0.20
RUN pip -v install joblib


#ENV PIP_NO_CACHE_DIR=1

##ensure no stale wheels
#RUN pip install --upgrade pip setuptools wheel
##RUN pip cache purge

# Upgrade pip and install dependencies
#RUN pip install --upgrade pip && \
#    pip install --no-cache-dir -r requirements.txt
#RUN pip install --upgrade pip
## RUN pip install --no-cache-dir -r requirements.txt
#RUN pip install --no-cache-dir -v -r requirements.txt

# ============================================================================
# PRODUCTION STAGE - Minimal runtime environment
# ============================================================================
FROM python:3.9-slim as production
#FROM python:3.11-slim as production
#FROM python:3.10.14-slim as production

# Set working directory
WORKDIR /app

# Install only runtime dependencies including libgomp1 for LightGBM
RUN apt-get update && apt-get install -y \
    libpq5 \
    curl \
    libgomp1 \
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

## Remove all .pyc files (avoiding stale/mismatched bytecode)
#RUN find . -name "*.pyc" -delete
# Remove all .pyc files using xargs (safer for large trees)
RUN find . -name "*.pyc" -print0 | xargs -0 rm -f

# Set Python path and other environment variables
ENV PYTHONPATH=/app \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONIOENCODING=utf-8

# Health check script
COPY --chown=mluser:mluser healthcheck.py /app/healthcheck.py
RUN chmod +x /app/healthcheck.py

# Switch to non-root user
USER mluser

# Expose port
EXPOSE 8001

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD python /app/healthcheck.py

# test
#RUN ls -lR /app/src

# Start command with proper signal handling
CMD ["python", "-m", "uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8001", "--workers", "1"]

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
