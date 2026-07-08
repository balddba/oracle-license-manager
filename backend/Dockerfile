# syntax=docker/dockerfile:1

FROM python:3.13-slim AS base

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    PYTHONUNBUFFERED=1 \
    LICENSE_TRACKER_CONFIG_PATH=/app/config/license-tracker.yaml

COPY backend/pyproject.toml /app/backend/
COPY backend/alembic.ini /app/backend/
COPY backend/alembic /app/backend/alembic
COPY backend/scripts/echarts-renderer /app/backend/scripts/echarts-renderer
COPY backend/src /app/backend/src

WORKDIR /app/backend
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        nodejs \
        npm \
        libcairo2-dev \
        libpango1.0-dev \
        libjpeg-dev \
        libgif-dev \
        librsvg2-dev \
        build-essential \
        python3-dev \
    && cd /app/backend/scripts/echarts-renderer && npm ci \
    && apt-get purge -y build-essential python3-dev \
    && apt-get autoremove -y \
    && rm -rf /var/lib/apt/lists/* \
    && uv sync --no-dev

ENV LICENSE_TRACKER_ECHARTS_RENDERER=/app/backend/scripts/echarts-renderer

COPY config /app/config
COPY data /app/data

WORKDIR /app
ENV PATH="/app/backend/.venv/bin:${PATH}"

RUN mkdir -p /app/data

EXPOSE 8000

CMD ["uvicorn", "license_tracker.main:app", "--host", "0.0.0.0", "--port", "8000"]
