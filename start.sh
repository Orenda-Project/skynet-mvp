#!/bin/bash
set -e  # Exit on error
set -x  # Print commands as they're executed

echo "========================================"
echo "=== SkyNet Startup Script Starting ===="
echo "========================================"
echo "PORT: ${PORT:-8000}"
echo "DATABASE_URL: ${DATABASE_URL:0:30}..."
echo ""

echo "[1/2] Running Alembic migrations..."
alembic upgrade head -v
echo ""
echo "[1/2] ✓ Migrations completed successfully!"
echo ""

echo "[2/2] Starting Uvicorn server..."
exec uvicorn src.main:app --host 0.0.0.0 --port ${PORT:-8000} --log-level info
