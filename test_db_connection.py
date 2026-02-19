#!/usr/bin/env python
"""
Test database connection and check schema.
"""
import sys
import os

# Add src to path
sys.path.insert(0, os.path.dirname(__file__))

print("=" * 60)
print("Testing Supabase Database Connection")
print("=" * 60)

try:
    print("\n1. Loading environment variables...")
    from dotenv import load_dotenv
    load_dotenv()
    print("   [OK] Environment loaded")

    print("\n2. Importing config...")
    from src.config import settings
    print(f"   [OK] Config loaded")
    print(f"   - Environment: {settings.environment}")
    print(f"   - Debug: {settings.debug}")

    print("\n3. Getting database URL...")
    db_url = settings.get_database_url
    # Mask password
    import re
    masked = re.sub(r':([^:@]+)@', ':****@', db_url)
    print(f"   [OK] Database URL: {masked}")

    print("\n4. Creating engine...")
    from sqlalchemy import create_engine, text, inspect
    engine = create_engine(
        db_url,
        pool_pre_ping=True,
        connect_args={"connect_timeout": 10}
    )
    print("   [OK] Engine created")

    print("\n5. Testing connection...")
    with engine.connect() as conn:
        result = conn.execute(text("SELECT version()"))
        version = result.fetchone()[0]
        print(f"   [OK] Connected to PostgreSQL!")
        print(f"   - Version: {version[:50]}...")

    print("\n6. Checking existing tables...")
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    print(f"   - Found {len(tables)} tables:")
    for table in tables:
        print(f"     * {table}")

    if 'conversations' in tables:
        print("\n7. Checking 'conversations' table schema...")
        columns = inspector.get_columns('conversations')
        print(f"   - {len(columns)} columns:")
        for col in columns:
            print(f"     * {col['name']}: {col['type']}")

    if 'alembic_version' in tables:
        print("\n8. Checking Alembic version...")
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version_num FROM alembic_version"))
            version_num = result.fetchone()
            if version_num:
                print(f"   - Current migration: {version_num[0]}")
            else:
                print("   - No migrations applied yet")

    print("\n9. Importing models to check for issues...")
    from src.models import Conversation, Participant, Synthesis
    print("   [OK] All models imported successfully")

    print("\n" + "=" * 60)
    print("[SUCCESS] DATABASE CONNECTION TEST PASSED!")
    print("=" * 60)

except Exception as e:
    print(f"\n[ERROR] {e}")
    print("\nFull traceback:")
    import traceback
    traceback.print_exc()
    sys.exit(1)
