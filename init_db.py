#!/usr/bin/env python
"""
Simple database initialization script.
Creates tables if they don't exist, then starts the server.
"""
import sys

print("=== SkyNet Database Initialization ===", flush=True)

try:
    print("Importing SQLAlchemy...", flush=True)
    from src.database.postgres import engine, Base
    print("✓ SQLAlchemy imported", flush=True)

    print("Importing models...", flush=True)
    from src.models import Conversation, Participant, Synthesis
    print("✓ Models imported", flush=True)

    print("Creating database tables (if they don't exist)...", flush=True)
    Base.metadata.create_all(bind=engine)
    print("✓ Tables created successfully!", flush=True)

except Exception as e:
    print(f"✗ Database initialization failed: {e}", file=sys.stderr, flush=True)
    import traceback
    traceback.print_exc()
    print("\nContinuing anyway - tables may already exist...", flush=True)

print("\n=== Starting Uvicorn Server ===", flush=True)
import os
import uvicorn

port = int(os.getenv("PORT", "8000"))
print(f"Listening on port {port}...\n", flush=True)

uvicorn.run(
    "src.main:app",
    host="0.0.0.0",
    port=port,
    log_level="info"
)
