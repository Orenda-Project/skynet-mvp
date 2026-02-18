#!/bin/bash
set -e  # Exit on error

echo "=== SkyNet Startup Script ==="
echo "Starting database migrations..."

# Run Alembic migrations with verbose output
alembic upgrade head -v

echo "Migrations completed successfully!"
echo "Starting uvicorn server..."

# Start uvicorn
exec uvicorn src.main:app --host 0.0.0.0 --port ${PORT:-8000} --log-level info
