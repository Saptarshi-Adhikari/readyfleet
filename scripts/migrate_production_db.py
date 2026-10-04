"""
READYFLEET Production Database Migration Script
==============================================
Verifies PostgreSQL connection using DATABASE_URL, creates missing schema tables,
and applies safe schema migrations idempotently without destroying existing data.
"""

import sys
import os

# Add repo root to python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from gen.db import get_database_backend, init_db, get_connection, SCHEMA_PATH, convert_sqlite_schema_to_postgres

def migrate():
    backend = get_database_backend()
    print(f"[MIGRATION] Database backend detected: {backend}")
    if backend not in ("postgres", "postgresql"):
        print("[MIGRATION NOTICE] DATABASE_BACKEND is not postgres. Initializing SQLite database...")
        init_db()
        print("[MIGRATION SUCCESS] SQLite database initialized.")
        return

    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        print("[MIGRATION ERROR] DATABASE_URL is missing!")
        sys.exit(1)

    print(f"[MIGRATION] Connecting to PostgreSQL...")
    try:
        conn = get_connection()
        with conn:
            with conn.cursor() as cur:
                with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
                    schema_sql = f.read()
                pg_sql = convert_sqlite_schema_to_postgres(schema_sql)
                cur.execute(pg_sql)
        conn.close()
        print("[MIGRATION SUCCESS] PostgreSQL schema verified and updated successfully.")
    except Exception as e:
        print(f"[MIGRATION ERROR] Failed to migrate PostgreSQL database: {e}")
        sys.exit(1)

if __name__ == "__main__":
    migrate()
