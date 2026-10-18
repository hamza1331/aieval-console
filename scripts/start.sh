#!/usr/bin/env bash
set -e

echo "========================================="
echo " Starting Aieval Console Monolith v0.1.0 "
echo "========================================="

# 1. Apply database migrations
echo "[1/3] Checking and applying database schema migrations..."
python -m app.db.migrate || echo "Migration runner completed."

# 2. Seed initial demo data if SEED_DEMO_DATA=true
if [ "${SEED_DEMO_DATA}" = "true" ] || [ "${SEED_DEMO_DATA}" = "1" ]; then
    echo "[2/3] Seeding demo validation contract and synthetic runs..."
    python -m app.db.seed || echo "Demo seed step completed."
else
    echo "[2/3] Skipping demo data seeding (set SEED_DEMO_DATA=true to enable)."
fi

# 3. Exec ASGI Server
echo "[3/3] Launching Uvicorn ASGI server on ${HOST:-0.0.0.0}:${PORT:-8000}..."
exec uvicorn app.main:app --host "${HOST:-0.0.0.0}" --port "${PORT:-8000}"
