# Railway Dockerfile - placed at repository root
# Handles studypulse/backend path internally

FROM python:3.11-slim

# Security: Create non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Install minimal system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    libffi-dev \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# CACHE BUST: 2026-02-17T09:25:00Z - Force rebuild for bcrypt fix
# Copy backend requirements from subdirectory
COPY studypulse/backend/requirements-railway.txt requirements.txt

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy entire backend directory
COPY studypulse/backend /app/

# Create necessary directories
RUN mkdir -p /app/data /app/logs && \
    chown -R appuser:appuser /app/data /app/logs /app

# Switch to non-root user
USER appuser

# Expose port (Railway sets $PORT dynamically)
EXPOSE 8000

# Start application
CMD find /app -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true; \
    find /app -type f -name '*.pyc' -delete 2>/dev/null || true; \
    echo "✅ Python cache cleared"; \
    exec gunicorn app.main:app \
    --workers 2 \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind 0.0.0.0:${PORT:-8000} \
    --timeout 120 \
    --keep-alive 5 \
    --access-logfile - \
    --error-logfile -
