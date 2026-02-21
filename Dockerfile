# ── Stage 1: build ────────────────────────────────────────────────────────────
FROM python:3.13-slim AS base

WORKDIR /app

# Install dependencies first (layer caching)
COPY pyproject.toml .
RUN pip install --no-cache-dir uv && \
    uv pip install --system \
        fastapi \
        uvicorn \
        openmeteo-requests \
        requests-cache \
        retry-requests \
        pandas \
        numpy \
        requests

# Copy source
COPY llm.py intent.py weather.py main.py ./
COPY static/ ./static/

# ── Runtime ────────────────────────────────────────────────────────────────────
ENV PYTHONUNBUFFERED=1
EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
