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
# torch CPU wheel: Aliyun pytorch-wheels 优先（服务器同网络，快），SJTU 兜底
# timeout 1200 = 20 分钟上限，超时即失败（不再无限挂起）
RUN --mount=type=cache,target=/root/.cache/uv \
    timeout 1200 uv pip install --python .venv/bin/python torch \
    --index-url https://mirrors.aliyun.com/pytorch-wheels/cpu/ \
    --extra-index-url https://mirror.sjtu.edu.cn/pytorch-wheels/cpu/ \
    --extra-index-url https://mirrors.aliyun.com/pypi/simple/
# Install remaining dependencies from lockfile, skipping torch (already installed)
# CPU torch 不需要 nvidia CUDA 包——lockfile 含 CUDA 依赖（开发者机器生成），
# uv sync 装它们会下载 15GB+ nvidia 包且超时。--no-install-package 全部跳过。
# UV_DEFAULT_INDEX: Aliyun PyPI mirror for CN servers
# UV_HTTP_TIMEOUT=300: 单请求 5 分钟无响应即失败（不无限挂起）
# timeout 600 = uv sync 10 分钟上限
ENV UV_DEFAULT_INDEX=https://mirrors.aliyun.com/pypi/simple/ \
    UV_HTTP_TIMEOUT=300
RUN --mount=type=cache,target=/root/.cache/uv \
    timeout 600 uv sync --frozen --no-dev \
    --no-install-package torch \
    --no-install-package nvidia-cublas \
    --no-install-package nvidia-cuda-cupti \
    --no-install-package nvidia-cuda-nvrtc \
    --no-install-package nvidia-cuda-runtime \
    --no-install-package nvidia-cudnn-cu13 \
    --no-install-package nvidia-cufft \
    --no-install-package nvidia-cufile \
    --no-install-package nvidia-curand \
    --no-install-package nvidia-cusolver \
    --no-install-package nvidia-cusparse \
    --no-install-package nvidia-cusparselt-cu13 \
    --no-install-package nvidia-nccl-cu13 \
    --no-install-package nvidia-nvjitlink \
    --no-install-package nvidia-nvshmem-cu13 \
    --no-install-package nvidia-nvtx

# Make venv binaries available on PATH
ENV PATH="/app/.venv/bin:$PATH"

# Copy application code
COPY backend/ ./

# HuggingFace model cache — persist via volume mounted at /data/hf_cache
ENV HF_HOME=/data/hf_cache

EXPOSE 8000

# Run migrations (DATABASE_URL from env, see migrations/env.py) then start the API server
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"]