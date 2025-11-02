# ═══════════════════════════════════════════════════════════════════
# Alert & Maintenance Service - Production-Hardened Dockerfile
# ═══════════════════════════════════════════════════════════════════

# ───────────────────────────────────────────────────────────────────
# Stage 1: Builder - Compile dependencies with all build tools
# ───────────────────────────────────────────────────────────────────
FROM python:3.11-slim as builder

WORKDIR /build

# Set Python environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copy requirements and build wheels
COPY requirements.txt .
RUN pip install --user --no-warn-script-location \
    --compile \
    -r requirements.txt

# ───────────────────────────────────────────────────────────────────
# Stage 2: Runtime - Minimal security-hardened image
# ───────────────────────────────────────────────────────────────────
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH=/home/appuser/.local/bin:$PATH

# Best Practice: Create non-root user for security
RUN groupadd -r appuser && useradd -r -g appuser -u 1000 appuser

# Install runtime dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

WORKDIR /app

# Copy compiled dependencies from builder
COPY --from=builder --chown=appuser:appuser /root/.local /home/appuser/.local

# Copy application code
COPY --chown=appuser:appuser app/ ./app/

# Set restrictive file permissions
RUN chmod -R 555 /app && \
    chmod 755 /app

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 8003

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8003/health || exit 1

# Proper signal handling
ENTRYPOINT ["python", "-m", "uvicorn"]
CMD ["app.main:app", "--host", "0.0.0.0", "--port", "8003", "--workers", "1"]
