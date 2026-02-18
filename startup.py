#!/usr/bin/env python
"""
Startup script for Railway deployment.
Runs Alembic migrations before starting the uvicorn server.
"""
import sys
import os

# Force unbuffered output
print("STARTUP: Python script starting...", flush=True)

try:
    from alembic.config import Config
    from alembic import command
    print("STARTUP: Alembic imports successful", flush=True)
except Exception as e:
    print(f"STARTUP ERROR: Failed to import Alembic: {e}", file=sys.stderr, flush=True)
    import traceback
    traceback.print_exc()
    sys.exit(1)

def run_migrations():
    """Run Alembic migrations."""
    print("=" * 60)
    print("Starting SkyNet - Running database migrations...")
    print("=" * 60)

    try:
        # Create Alembic configuration
        alembic_cfg = Config("alembic.ini")

        # Run migrations
        print("Running: alembic upgrade head")
        command.upgrade(alembic_cfg, "head")

        print("✓ Migrations completed successfully!")
        print("=" * 60)
        return True

    except Exception as e:
        print(f"✗ Migration failed: {e}", file=sys.stderr)
        print(f"Error type: {type(e).__name__}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return False

def start_uvicorn():
    """Start the uvicorn server."""
    import uvicorn

    port = int(os.getenv("PORT", "8000"))
    print(f"Starting uvicorn server on port {port}...")

    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=port,
        log_level="info"
    )

if __name__ == "__main__":
    print(f"Python version: {sys.version}", flush=True)
    print(f"Working directory: {os.getcwd()}", flush=True)
    print(f"PORT: {os.getenv('PORT', '8000')}", flush=True)
    print("", flush=True)

    # Run migrations
    if run_migrations():
        # Start server
        start_uvicorn()
    else:
        print("Failed to run migrations. Exiting.", file=sys.stderr, flush=True)
        sys.exit(1)
