"""
Supabase PostgreSQL database connection management.
Follows Guardrail #3: Dependency Injection (connections are injected, not hardcoded)
"""

from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

from src.config import settings

# Get database URL from Supabase configuration
database_url = settings.get_database_url

# DEBUG: Log the constructed database URL (mask password)
import re
masked_url = re.sub(r':([^:@]+)@', ':****@', database_url)
print(f"[DATABASE] Connecting to Supabase: {masked_url}")

# Convert postgres:// to postgresql:// for SQLAlchemy 2.0+ with psycopg2
if database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)
    print(f"[DATABASE] Converted to: {re.sub(r':([^:@]+)@', ':****@', database_url)}")

# Create database engine
# pool_pre_ping=True ensures connections are alive before using them
# connect_timeout prevents hanging on connection issues
try:
    engine = create_engine(
        database_url,
        pool_pre_ping=True,
        pool_size=5,
        max_overflow=10,
        echo=settings.debug,  # Log SQL queries in debug mode
        connect_args={"connect_timeout": 10}  # 10 second timeout
    )
    print("[DATABASE] Engine created successfully")
except Exception as e:
    print(f"[DATABASE ERROR] Failed to create engine: {e}")
    raise

# Create session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# Base class for all models
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """
    Dependency injection function for database sessions.
    Used with FastAPI's Depends() to inject database sessions into routes.

    Usage:
        @app.get("/items")
        def get_items(db: Session = Depends(get_db)):
            return db.query(Item).all()

    The session is automatically closed after the request completes.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """
    Initialize database tables.
    This should only be used in development/testing.
    In production, use Alembic migrations instead.
    """
    Base.metadata.create_all(bind=engine)


def drop_db() -> None:
    """
    Drop all database tables.
    ⚠️ DANGER: This will delete all data!
    Only use in testing.
    """
    Base.metadata.drop_all(bind=engine)
