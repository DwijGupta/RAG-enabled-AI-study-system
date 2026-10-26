# ==============================================================================
# AI Study Buddy Backend - Production Dockerfile (Security Hardened)
# ==============================================================================

# Stage 1: Build & Dependencies
FROM python:3.11-slim AS builder

WORKDIR /build

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Stage 2: Minimal Secure Runtime
FROM python:3.11-slim AS runtime

# Install runtime libraries for PyMuPDF (fitz) and curl for healthcheck
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    libmupdf-dev \
    && rm -rf /var/lib/apt/lists/*

# Security: Create non-root system user and group
RUN groupadd -g 10001 appgroup && \
    useradd -u 10001 -g appgroup -s /bin/bash -m appuser

WORKDIR /app

# Copy python dependencies from builder
COPY --from=builder /root/.local /home/appuser/.local

# Copy application source code
COPY --chown=appuser:appgroup app /app/app
COPY --chown=appuser:appgroup seed_kb.py /app/seed_kb.py
COPY --chown=appuser:appgroup requirements.txt /app/requirements.txt

# Create storage and data directories with secure ownership
RUN mkdir -p /app/data/storage/pages /app/data/storage/uploads && \
    chown -R appuser:appgroup /app/data

# Switch to unprivileged user
USER appuser
ENV PATH="/home/appuser/.local/bin:${PATH}" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH="/app"

EXPOSE 8000

# Continuous Container Healthcheck
HEALTHCHECK --interval=20s --timeout=5s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8000/api/health || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
