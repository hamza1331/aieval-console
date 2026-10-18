# syntax=docker/dockerfile:1
# Multi-stage Dockerfile for Aieval Console (v0.1.0 Unified Monolith)

# ==========================================
# Stage 1: Build React / TypeScript Frontend
# ==========================================
FROM node:22-alpine AS frontend-builder
WORKDIR /build

# Copy npm package definitions
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci

# Copy frontend source and compile production bundle into /build/dist
COPY frontend/ ./
RUN npm run build

# ==========================================
# Stage 2: FastAPI + aieval-py Runner
# ==========================================
FROM python:3.12-slim AS runner

WORKDIR /app

# Install system dependencies (curl for container healthcheck)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Runtime environment configuration
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    HOST=0.0.0.0 \
    PORT=8000 \
    DATA_DIR=/app/data \
    DATABASE_URL=sqlite:////app/data/aieval.db \
    AUTO_MIGRATE=true \
    STATIC_DIR=/app/frontend/dist

# Install core library aieval-py
COPY aieval-py* /aieval-py/
RUN if [ -d "/aieval-py/src" ]; then pip install --no-cache-dir /aieval-py; fi

# Install backend dependencies & package
WORKDIR /app/backend
COPY backend/pyproject.toml backend/alembic.ini /app/backend/
COPY backend/alembic /app/backend/alembic
COPY backend/app /app/backend/app

RUN pip install --no-cache-dir .

# Copy compiled frontend assets from Stage 1
COPY --from=frontend-builder /build/dist /app/frontend/dist

# Copy entrypoint startup script
COPY scripts/start.sh /app/scripts/start.sh
RUN chmod +x /app/scripts/start.sh

# Persistent SQLite database volume mount point
RUN mkdir -p /app/data

EXPOSE 8000

HEALTHCHECK --interval=10s --timeout=5s --start-period=5s --retries=3 \
  CMD curl -f http://127.0.0.1:8000/health || exit 1

ENTRYPOINT ["/app/scripts/start.sh"]
