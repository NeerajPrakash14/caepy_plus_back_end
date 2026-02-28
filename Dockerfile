# ============================================
# Doctor Onboarding Service - Production Dockerfile
# ============================================
# Multi-stage build for optimized production image

# ----------------------------------------
# Stage 1: Build dependencies
# ----------------------------------------
FROM python:3.12-slim AS builder

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy only dependency files first (for caching)
COPY pyproject.toml ./

# Create virtual environment and install dependencies
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install dependencies
RUN pip install --upgrade pip && \
    pip install . && \
    pip install uvicorn[standard]

# ----------------------------------------
# Stage 2: Production image
# ----------------------------------------
FROM python:3.12-slim AS production

# Labels
LABEL maintainer="Your Name <your.email@example.com>"
LABEL org.opencontainers.image.title="Doctor Onboarding Service"
LABEL org.opencontainers.image.description="Production-grade doctor onboarding microservice"
LABEL org.opencontainers.image.version="2.0.0"

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONFAULTHANDLER=1 \
    PATH="/opt/venv/bin:$PATH" \
    APP_ENV=production \
    PORT=8000

# Create non-root user for security
RUN groupadd --gid 1000 appgroup && \
    useradd --uid 1000 --gid appgroup --shell /bin/bash --create-home appuser

WORKDIR /app

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv

# Copy application code
COPY --chown=appuser:appgroup src/ ./src/
COPY --chown=appuser:appgroup alembic/ ./alembic/
COPY --chown=appuser:appgroup alembic.ini ./
COPY --chown=appuser:appgroup pyproject.toml ./
# Email templates and other runtime YAML configs required at startup
COPY --chown=appuser:appgroup config/ ./config/

# Copy entrypoint script (runs migrations then starts uvicorn)
COPY --chown=appuser:appgroup entrypoint.sh ./entrypoint.sh
RUN chmod +x /app/entrypoint.sh

# Create data directory for local blob storage / temp files
RUN mkdir -p /app/data && chown appuser:appgroup /app/data

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 8000

# Health check — uses the liveness probe (no DB dependency, always lightweight).
# The readiness probe (/api/v1/ready) is left to the orchestrator (K8s/ECS)
# because it requires a live DB connection and should not restart the container
# on transient DB blips.
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD python -c "import urllib.request, sys; r = urllib.request.urlopen('http://localhost:8000/api/v1/live', timeout=8); sys.exit(0 if r.status == 200 else 1)"

# ── ENTRYPOINT ────────────────────────────────────────────────────────────────
# entrypoint.sh performs three steps on every container start:
#   1. Waits for PostgreSQL to be reachable
#   2. Runs `alembic upgrade head` (idempotent — no-op if already up to date)
#   3. Starts uvicorn
#
# docker-compose.yml overrides ENTRYPOINT with entrypoint.sh.
# The CMD here is the fallback for plain `docker run` invocations.
ENTRYPOINT ["/app/entrypoint.sh"]

# ── WORKER COUNT AND SESSION STORE COMPATIBILITY ──────────────────────────────
# The voice-onboarding feature uses InMemorySessionStore by default.
# InMemorySessionStore is process-local: each worker holds its own in-memory
# session map.  A session created by worker A is invisible to workers B/C/D —
# requests that land on a different worker will receive 404 or 410.
#
# Keep UVICORN_WORKERS=1 (env var read by entrypoint.sh) until a Redis-backed
# session store is configured.
#
#   ✓ Safe now  (single worker, no shared session store needed):
#       UVICORN_WORKERS=1   ← default in entrypoint.sh
#
#   High-throughput (only safe once Redis session store is wired in):
#       UVICORN_WORKERS=4
