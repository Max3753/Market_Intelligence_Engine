# Backend Dockerfile — FastAPI + Crawlee (production)
FROM python:3.12-slim AS base

# Prevent Python from writing .pyc files and enable unbuffered output
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Install uv for fast dependency management
# Aliyun PyPI mirror for CN servers (fallback: default PyPI)
RUN pip install --no-cache-dir -i https://mirrors.aliyun.com/pypi/simple/ uv

WORKDIR /app

# Copy dependency files first for layer caching
COPY backend/pyproject.toml backend/uv.lock* backend/README.md ./

# Create venv and install CPU-only torch first — sentence-transformers pulls CUDA
# torch (~2.5GB) from the default index; CPU build (~200MB) is enough for inference.
# SJTU pytorch-wheels mirror has torch CPU wheels (Aliyun mirror lacks torch);
# deps resolve from Aliyun PyPI via --extra-index-url.
RUN uv venv
RUN --mount=type=cache,target=/root/.cache/uv \
    uv pip install --python .venv/bin/python torch \
    --index-url https://mirror.sjtu.edu.cn/pytorch-wheels/cpu/ \
    --extra-index-url https://mirrors.aliyun.com/pypi/simple/
# Install remaining dependencies from lockfile, skipping torch (already installed)
# UV_DEFAULT_INDEX: Aliyun PyPI mirror for CN servers
ENV UV_DEFAULT_INDEX=https://mirrors.aliyun.com/pypi/simple/
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --no-install-package torch

# Make venv binaries available on PATH
ENV PATH="/app/.venv/bin:$PATH"

# Copy application code
COPY backend/ ./

# HuggingFace model cache — persist via volume mounted at /data/hf_cache
ENV HF_HOME=/data/hf_cache

EXPOSE 8000

# Run migrations (DATABASE_URL from env, see migrations/env.py) then start the API server
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"]