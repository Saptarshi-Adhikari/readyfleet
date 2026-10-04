import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "readyfleet.db")
SCHEMA_PATH = os.path.join(os.path.dirname(__file__), "schema.sql")

def get_connection(db_path: str = DB_PATH) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def init_db(db_path: str = DB_PATH, schema_path: str = SCHEMA_PATH) -> None:
    if os.path.exists(db_path):
        try:
            os.remove(db_path)
        except PermissionError:
            # File is locked by another process (e.g. background server); re-initialize in-place
            pass
    with open(schema_path, "r", encoding="utf-8") as f:
        schema_sql = f.read()
    conn = get_connection(db_path)
    with conn:
        conn.executescript(schema_sql)
    conn.close()

if __name__ == "__main__":
    init_db()
    print(f"Initialized database successfully at {DB_PATH}")
