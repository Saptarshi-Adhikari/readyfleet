"""
READYFLEET Database Connection & Storage Adapter
=================================================
Supports dual database backends:
- SQLite (DATABASE_BACKEND=sqlite): For local development and unit tests.
- PostgreSQL (DATABASE_BACKEND=postgres): Serverless-safe persistent database for Vercel production.
"""

import sqlite3
import os
from typing import Any

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "readyfleet.db")
SCHEMA_PATH = os.path.join(os.path.dirname(__file__), "schema.sql")

def get_database_backend() -> str:
    backend = os.environ.get("DATABASE_BACKEND")
    if not backend:
        db_url = os.environ.get("DATABASE_URL", "")
        if db_url.startswith("postgres://") or db_url.startswith("postgresql://"):
            return "postgres"
        return "sqlite"
    return backend.lower()

def convert_sqlite_schema_to_postgres(sql: str) -> str:
    sql = sql.replace("INTEGER PRIMARY KEY AUTOINCREMENT", "SERIAL PRIMARY KEY")
    sql = sql.replace("DATETIME", "TIMESTAMP WITH TIME ZONE")
    lines = [l for l in sql.splitlines() if not l.strip().startswith("PRAGMA")]
    return "\n".join(lines)

def get_connection(db_path: str = DB_PATH) -> Any:
    backend = get_database_backend()
    if backend in ("postgres", "postgresql"):
        db_url = os.environ.get("DATABASE_URL")
        if not db_url:
            raise RuntimeError("DATABASE_BACKEND is set to postgres but DATABASE_URL environment variable is missing or empty.")
        if db_url.startswith("postgres://"):
            db_url = db_url.replace("postgres://", "postgresql://", 1)
        import psycopg2
        import psycopg2.extras
        conn = psycopg2.connect(db_url, cursor_factory=psycopg2.extras.DictCursor)
        return conn
    else:
        # SQLite local dev / testing fallback
        try:
            conn = sqlite3.connect(db_path)
        except sqlite3.OperationalError:
            # Fallback to /tmp if local filesystem is read-only
            tmp_db = os.path.join("/tmp", "readyfleet.db")
            conn = sqlite3.connect(tmp_db)

        conn.row_factory = sqlite3.Row
        try:
            conn.execute("PRAGMA foreign_keys = ON;")
        except Exception:
            pass
        return conn

def init_db(db_path: str = DB_PATH, schema_path: str = SCHEMA_PATH) -> None:
    backend = get_database_backend()
    with open(schema_path, "r", encoding="utf-8") as f:
        schema_sql = f.read()

    if backend in ("postgres", "postgresql"):
        conn = get_connection(db_path)
        pg_sql = convert_sqlite_schema_to_postgres(schema_sql)
        with conn:
            with conn.cursor() as cur:
                cur.execute(pg_sql)
        conn.close()
    else:
        if os.path.exists(db_path):
            try:
                os.remove(db_path)
            except (PermissionError, sqlite3.OperationalError):
                pass
        conn = sqlite3.connect(db_path)
        with conn:
            conn.executescript(schema_sql)
        conn.close()

if __name__ == "__main__":
    init_db()
    print(f"Initialized database successfully for backend '{get_database_backend()}'.")
