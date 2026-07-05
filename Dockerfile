# Dockerfile — AXIOM FastAPI backend image.
FROM python:3.11-slim AS base

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# System deps: build tools for native wheels (tree-sitter, asyncpg).
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential curl \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml README.md ./
COPY axiom ./axiom
COPY alembic ./alembic
COPY alembic.ini ./

# Install the base package (ML/eBPF extras are installed separately per-environment).
RUN pip install --upgrade pip && pip install .

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD curl -fsS http://localhost:8000/health || exit 1

CMD ["uvicorn", "axiom.main:app", "--host", "0.0.0.0", "--port", "8000"]
