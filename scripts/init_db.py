"""Initialise and verify the MFIP DuckDB schema.

Idempotent with three-case behaviour:

- **Empty DB** — no application tables found: apply the full schema
  from ``mfip/logging/schema.sql`` inside a transaction. Reports the
  number of tables created. Exits 0.
- **Schema current** — every expected table and column present with
  matching type and nullability: reports "no changes" and exits 0.
- **Schema drift** — application tables present but they don't match
  expectations: prints a summary of the diff (verbose flag adds the
  per-column detail) and exits 1 without modifying the DB. The
  operator decides next steps manually.

DB path resolution: ``MFIP_DB_PATH`` env var, falling back to
``C:\\MFIP\\runtime\\mfip.duckdb``. The parent directory is created
if missing.

EXPECTED_SCHEMA below is the authoritative shape this script
verifies against. Update it whenever ``mfip/logging/schema.sql``
changes. We use an explicit dict rather than parsing the SQL
because the SQL has CHECK constraints, multi-line statements, and
implicit type normalisations (TEXT → VARCHAR, VARCHAR(N) → VARCHAR)
that DuckDB's information_schema returns canonically; matching
against the canonical form is more reliable than parsing the source.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

import duckdb

DEFAULT_DB_PATH = Path(r"C:\MFIP\runtime\mfip.duckdb")
SCHEMA_PATH = (
    Path(__file__).resolve().parent.parent / "mfip" / "logging" / "schema.sql"
)

# Type alias: {table_name: {column_name: (data_type, nullable_bool)}}
ColumnSpec = tuple[str, bool]
TableSchema = dict[str, ColumnSpec]
DBSchema = dict[str, TableSchema]

# Authoritative expected shape. Types are DuckDB's canonical form as
# returned by information_schema.columns (probed empirically — TEXT,
# VARCHAR(N), and untyped VARCHAR all collapse to VARCHAR).
EXPECTED_SCHEMA: DBSchema = {
    "decision_log": {
        "id": ("UUID", False),
        "correlation_id": ("UUID", False),
        "timestamp": ("TIMESTAMP", False),
        "agent": ("VARCHAR", False),
        "decision_type": ("VARCHAR", False),
        "phase": ("VARCHAR", False),
        "ticker": ("VARCHAR", True),
        "confidence_score": ("DECIMAL(4,3)", True),
        "payload": ("JSON", False),
    },
    "security_log": {
        "log_id": ("UUID", False),
        "correlation_id": ("UUID", True),
        "timestamp": ("TIMESTAMP", False),
        "severity": ("VARCHAR", False),
        "issuing_agent": ("VARCHAR", False),
        "flagging_officer": ("VARCHAR", True),
        "issue_description": ("VARCHAR", False),
        "impact_assessment": ("VARCHAR", True),
        "recommended_action": ("VARCHAR", True),
        "pipeline_status": ("VARCHAR", True),
        "resolved_at": ("TIMESTAMP", True),
        "resolution_note": ("VARCHAR", True),
    },
}


def resolve_db_path() -> Path:
    return Path(os.environ.get("MFIP_DB_PATH", str(DEFAULT_DB_PATH)))


def _read_actual_schema(conn: duckdb.DuckDBPyConnection) -> DBSchema:
    """Reflect the live DB schema for tables in EXPECTED_SCHEMA."""
    actual: DBSchema = {}
    rows = conn.execute(
        """
        SELECT table_name, column_name, data_type, is_nullable
        FROM information_schema.columns
        WHERE table_schema = 'main' AND table_name IN (
            SELECT unnest(?)
        )
        ORDER BY table_name, ordinal_position
        """,
        (list(EXPECTED_SCHEMA),),
    ).fetchall()
    for table, column, dtype, nullable in rows:
        actual.setdefault(table, {})[column] = (dtype, nullable == "YES")
    return actual


def _list_application_tables(conn: duckdb.DuckDBPyConnection) -> set[str]:
    """Return the set of EXPECTED_SCHEMA tables that exist in the DB.

    Limits to known application tables so a stray test table or future
    unrelated table doesn't falsely trigger drift.
    """
    rows = conn.execute(
        """
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'main' AND table_name IN (
            SELECT unnest(?)
        )
        """,
        (list(EXPECTED_SCHEMA),),
    ).fetchall()
    return {row[0] for row in rows}


def _diff_schema(
    expected: DBSchema, actual: DBSchema
) -> dict[str, list[str]]:
    """Compute a structured diff: per-table list of human-readable
    discrepancies. Empty dict means schemas match.
    """
    diffs: dict[str, list[str]] = {}
    for table, exp_cols in expected.items():
        problems: list[str] = []
        act_cols = actual.get(table)
        if act_cols is None:
            problems.append("table missing")
            diffs[table] = problems
            continue
        missing = sorted(set(exp_cols) - set(act_cols))
        extra = sorted(set(act_cols) - set(exp_cols))
        for col in missing:
            problems.append(f"column missing: {col}")
        for col in extra:
            problems.append(f"unexpected column: {col}")
        for col in sorted(set(exp_cols) & set(act_cols)):
            exp = exp_cols[col]
            act = act_cols[col]
            if exp != act:
                problems.append(
                    f"column {col!r} differs: "
                    f"expected type={exp[0]} nullable={exp[1]}, "
                    f"actual type={act[0]} nullable={act[1]}"
                )
        if problems:
            diffs[table] = problems
    # Unexpected tables among EXPECTED_SCHEMA keys cannot appear here
    # (actual is built only from those keys); but flag any actual key
    # that isn't expected as a defensive check.
    for table in sorted(set(actual) - set(expected)):
        diffs.setdefault(table, []).append("unexpected table present")
    return diffs


def _apply_schema_transactional(conn: duckdb.DuckDBPyConnection) -> int:
    """Apply the schema SQL inside a transaction. Returns number of
    application tables present after commit. Rolls back on failure."""
    schema_sql = SCHEMA_PATH.read_text(encoding="utf-8")
    conn.execute("BEGIN TRANSACTION")
    try:
        conn.execute(schema_sql)
        conn.execute("COMMIT")
    except Exception:
        conn.execute("ROLLBACK")
        raise
    return len(_list_application_tables(conn))


def init_db(db_path: Path | None = None) -> Path:
    """Backwards-compatible entry point for tests.

    Applies the schema unconditionally to ``db_path``. Tests use fresh
    temp DBs so this is always Case A; production runs should go
    through ``main()`` to get the three-case behaviour.
    """
    db_path = db_path or resolve_db_path()
    db_path.parent.mkdir(parents=True, exist_ok=True)
    with duckdb.connect(str(db_path)) as conn:
        _apply_schema_transactional(conn)
    return db_path


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Initialise or verify the MFIP DuckDB schema. Idempotent — "
            "safe to re-run."
        )
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Print per-column drift detail on Case C.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv if argv is not None else sys.argv[1:])
    db_path = resolve_db_path()
    db_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"DB path: {db_path}")
    expected_tables = set(EXPECTED_SCHEMA)

    with duckdb.connect(str(db_path)) as conn:
        present = _list_application_tables(conn)

        # Case A: no application tables present.
        if not present:
            created = _apply_schema_transactional(conn)
            print(f"Schema applied. Created {created} tables.")
            return 0

        # Verify what's there.
        actual = _read_actual_schema(conn)
        diffs = _diff_schema(EXPECTED_SCHEMA, actual)

        # Also flag if any expected table is entirely absent (would be
        # an unusual "partial" state — some tables created, others not).
        missing_tables = sorted(expected_tables - present)
        for table in missing_tables:
            diffs.setdefault(table, []).append("table missing")

        # Case B: schema matches.
        if not diffs:
            print("Schema already current. No changes.")
            return 0

        # Case C: drift detected. Report and exit 1 without modifying.
        affected = sorted(diffs)
        print(
            f"Schema drift detected. Affected tables: {', '.join(affected)}."
        )
        if args.verbose:
            for table in affected:
                print(f"  [{table}]")
                for problem in diffs[table]:
                    print(f"    - {problem}")
        else:
            print("  Re-run with --verbose for per-column detail.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
