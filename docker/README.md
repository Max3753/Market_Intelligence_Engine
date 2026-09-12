# Docker Configurations

This directory contains Docker-related files for the Market Intelligence Engine.

## Files

| File | Description |
|---|---|
| `backend.Dockerfile` | Backend API container (FastAPI + Crawlee). Based on `python:3.12-slim`, installs `uv`, syncs dependencies, runs uvicorn on port 8000. |
| `frontend.Dockerfile` | Frontend web container (Next.js). Based on `node:22-alpine`, runs `npm ci` + `npm run build`, serves on port 3000. |
| `init-pgvector.sh` | PostgreSQL init script — installs the `pgvector` extension for vector similarity search (used in Phase 3+ for demand clustering). |

## Usage

```bash
# Build and run everything from the project root
docker compose up -d --build

# Build only the backend
docker build -f docker/backend.Dockerfile -t mie-backend .

# Build only the frontend
docker build -f docker/frontend.Dockerfile -t mie-frontend .
```

## Notes

- `init-pgvector.sh` runs automatically on first `docker compose up` to enable vector search in PostgreSQL.
- For production, consider adding a multi-stage build to reduce final image size.
- The `docker-compose.yml` in the project root manages PostgreSQL and Redis infrastructure.
