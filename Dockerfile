# syntax=docker/dockerfile:1
# CompostMitra — offline classroom image.
# Budget: <800MB, Streamlit cold start <30s (see compose comments).
# Layer order: requirements baked in builder before app code (final stage),
# so code edits reuse the cached venv layer.

# ── builder: venv at /opt/venv, inference-only (no xgboost/dev tools) ──
# Full ML/dev deps (xgboost, pytest, ruff) stay OUT of the image;
# gates profile installs them at CI time, never baked in.
FROM python:3.11-slim-bookworm AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.inference.txt .

# One RUN: venv + inference wheels only.
RUN python3 -m venv /opt/venv \
    && /opt/venv/bin/pip install --upgrade pip \
    && /opt/venv/bin/pip install --no-cache-dir -r requirements.inference.txt \
    && find /opt/venv -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true

# ── final: slim runtime, curl only, non-root ──
FROM python:3.11-slim-bookworm AS final

ENV PYTHONHASHSEED=42 \
    SEED=42 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH" \
    STREAMLIT_SERVER_PORT=8501 \
    STREAMLIT_SERVER_ADDRESS=0.0.0.0 \
    STREAMLIT_SERVER_HEADLESS=true

# One RUN: curl only + least-privilege system user (no home, no shell).
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --system --no-create-home --shell /usr/sbin/nologin app

WORKDIR /app

COPY --from=builder /opt/venv /opt/venv
COPY --chown=app:nogroup . .

USER app

EXPOSE 8501

# start-period 30s: model/metrics load + Streamlit cold start budget.
HEALTHCHECK --interval=10s --timeout=5s --retries=3 --start-period=30s \
    CMD curl -f http://localhost:8501/_stcore/health || exit 1

CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
