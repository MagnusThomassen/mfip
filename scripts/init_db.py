"""Initialise the MFIP DuckDB schema. Idempotent.

Resolves the DB path from MFIP_DB_PATH (default
`C:\\MFIP\\runtime\\mfip.duckdb`), creates the parent directory if
missing, opens a DuckDB connection, and executes
`mfip/logging/schema.sql`.

Safe to run multiple times — the schema uses IF NOT EXISTS throughout.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import duckdb

DEFAULT_DB_PATH = Path(r"C:\MFIP\runtime\mfip.duckdb")
SCHEMA_PATH = Path(__file__).resolve().parent.parent / "mfip" / "logging" / "schema.sql"


def resolve_db_path() -> Path:
    return Path(os.environ.get("MFIP_DB_PATH", str(DEFAULT_DB_PATH)))


def init_db(db_path: Path | None = None) -> Path:
    """Create the schema at `db_path` (default: env-resolved). Returns the
    path used."""
    db_path = db_path or resolve_db_path()
    db_path.parent.mkdir(parents=True, exist_ok=True)
    schema_sql = SCHEMA_PATH.read_text(encoding="utf-8")
    with duckdb.connect(str(db_path)) as conn:
        conn.execute(schema_sql)
    return db_path


def main() -> int:
    db_path = init_db()
    with duckdb.connect(str(db_path)) as conn:
        tables = [
            row[0]
            for row in conn.execute(
                "SELECT table_name FROM information_schema.tables "
                "WHERE table_schema = 'main' ORDER BY table_name"
            ).fetchall()
        ]
    print(f"DB path: {db_path}")
    print(f"Tables: {', '.join(tables) if tables else '(none)'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
