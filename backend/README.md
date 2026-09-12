# MIE Backend

FastAPI backend for Market Intelligence Engine.

## Quick Start

```bash
cp .env.example .env   # fill in your LLM_API_KEY
uv sync
uvicorn app.main:app --reload --port 8000
```

API docs: http://localhost:8000/docs
Health: http://localhost:8000/health
