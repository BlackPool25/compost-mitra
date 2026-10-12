# syntax=docker/dockerfile:1
# CompostMitra 2.0 — Production Dockerfile
# Multi-stage build: React 19 PWA frontend + FastAPI Python agronomic runtime.
# Zero Streamlit overhead, cold start < 1s, pure offline-first PWA.

# ── Stage 1: Build React 19 + TypeScript + Tailwind PWA ──
FROM node:24-slim AS frontend-builder

WORKDIR /app/frontend

COPY frontend/package*.json ./
RUN npm install

COPY frontend/ ./
RUN npm run build

# ── Stage 2: Python venv builder (FastAPI + inference packages) ──
FROM python:3.11-slim-bookworm AS python-builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.inference.txt .

RUN python3 -m venv /opt/venv \
    && /opt/venv/bin/pip install --upgrade pip \
    && /opt/venv/bin/pip install --no-cache-dir -r requirements.inference.txt \
    && find /opt/venv -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true

# ── Stage 3: Final Slim Production Runtime ──
FROM python:3.11-slim-bookworm AS final

ENV PYTHONHASHSEED=42 \
    SEED=42 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH" \
    PORT=3000

# Install curl for healthcheck and setup non-root user
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --system --no-create-home --shell /usr/sbin/nologin app

WORKDIR /app

# Copy python dependencies and compiled React PWA
COPY --from=python-builder /opt/venv /opt/venv
COPY --from=frontend-builder --chown=app:nogroup /app/frontend/dist /app/frontend/dist

# Copy application code and agronomic datasets
COPY --chown=app:nogroup . .

USER app

EXPOSE 3000

# Healthcheck targeting FastAPI /api/health endpoint
HEALTHCHECK --interval=10s --timeout=5s --retries=3 --start-period=10s \
    CMD curl -f http://localhost:3000/api/health || exit 1

CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "3000"]
