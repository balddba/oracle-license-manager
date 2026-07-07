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
COPY backend/src /app/backend/src

WORKDIR /app/backend
RUN uv sync --no-dev

COPY config /app/config
COPY data /app/data

WORKDIR /app
ENV PATH="/app/backend/.venv/bin:${PATH}"

RUN mkdir -p /app/data

EXPOSE 8000

CMD ["uvicorn", "license_tracker.main:app", "--host", "0.0.0.0", "--port", "8000"]
