"""Migration tuần tự, ghi schema_version."""

import sqlite3
from pathlib import Path

SCHEMA = Path(__file__).with_name("schema.sql")
MIGRATIONS: list[str] = [
    SCHEMA.read_text(encoding="utf-8"),  # v1
]


def connect(db_path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path, check_same_thread=False, isolation_level=None)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def migrate(conn: sqlite3.Connection) -> int:
    conn.execute("CREATE TABLE IF NOT EXISTS schema_version (version INTEGER NOT NULL)")
    row = conn.execute("SELECT MAX(version) AS v FROM schema_version").fetchone()
    current = row["v"] or 0
    for i, sql in enumerate(MIGRATIONS, start=1):
        if i > current:
            conn.executescript(sql)
            conn.execute("INSERT INTO schema_version(version) VALUES (?)", (i,))
            current = i
    return current
