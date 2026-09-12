# Backend Dockerfile — FastAPI + Crawlee (production)
FROM python:3.12-slim AS base

# Prevent Python from writing .pyc files and enable unbuffered output
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Install uv for fast dependency management
RUN pip install --no-cache-dir uv

WORKDIR /app

# Copy dependency files first for layer caching
COPY backend/pyproject.toml backend/uv.lock* backend/README.md ./

# Create venv and install CPU-only torch first — sentence-transformers pulls CUDA
# torch (~2.5GB) from the default index; CPU build (~200MB) is enough for inference.
RUN uv venv
RUN uv pip install --python .venv/bin/python torch --index-url https://download.pytorch.org/whl/cpu
# Install remaining dependencies from lockfile, skipping torch (already installed)
RUN uv sync --frozen --no-dev --no-install-package torch

# Make venv binaries available on PATH
ENV PATH="/app/.venv/bin:$PATH"

# Copy application code
COPY backend/ ./

# HuggingFace model cache — persist via volume mounted at /data/hf_cache
ENV HF_HOME=/data/hf_cache

EXPOSE 8000

# Run migrations (DATABASE_URL from env, see migrations/env.py) then start the API server
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"]