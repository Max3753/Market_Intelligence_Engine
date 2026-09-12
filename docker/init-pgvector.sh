#!/bin/bash
# Install pgvector extension for vector similarity search (Phase 3+)
set -e

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    CREATE EXTENSION IF NOT EXISTS vector;
EOSQL

echo "pgvector extension initialized."
