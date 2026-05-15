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
import importlib.util
import json
import os
import sys
from datetime import UTC, datetime
from pathlib import Path
from types import ModuleType

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


def _discover_migrations() -> list[tuple[str, ModuleType]]:
    """Discover migration modules in `mfip/logging/migrations/`.

    Returns ``[(filename, module), ...]`` ordered by the integer
    prefix of the filename (`001_*.py`, `002_*.py`, …). Files not
    matching `NNN_*.py` are ignored. See decisions.md 2026-05-15
    "Migrations module refactor: discoverable package, no schema
    version tracking in v1".

    Modules are loaded by absolute file path via ``importlib.util``
    rather than ``import_module`` so this works whether the script
    is invoked as ``python scripts/init_db.py`` (script-on-sys.path)
    or ``python -m mfip.something`` (package-on-sys.path).
    """
    pkg_path = (
        Path(__file__).resolve().parent.parent
        / "mfip"
        / "logging"
        / "migrations"
    )
    migration_files = sorted(
        pkg_path.glob("[0-9][0-9][0-9]_*.py"),
        key=lambda p: int(p.stem.split("_", 1)[0]),
    )
    discovered: list[tuple[str, ModuleType]] = []
    for f in migration_files:
        module_name = f"mfip.logging.migrations.{f.stem}"
        spec = importlib.util.spec_from_file_location(module_name, f)
        if spec is None or spec.loader is None:
            raise ImportError(f"Could not build spec for migration {f}")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        discovered.append((f.name, module))
    return discovered


def _read_table_rows(
    conn: duckdb.DuckDBPyConnection, table: str
) -> tuple[list[str], list[dict]]:
    """Fetch all rows from `table` as a list of column-keyed dicts.

    Returns (column_names_in_order, rows). Empty list when table is empty.
    """
    cursor = conn.execute(f"SELECT * FROM {table}")
    columns = [desc[0] for desc in cursor.description]
    raw = cursor.fetchall()
    rows = [dict(zip(columns, tup)) for tup in raw]
    return columns, rows


def _migration_dump_path(db_path: Path) -> Path:
    """Resolve the pre-migration dump path. Co-located with the DB file's
    parent directory under a `migrations/` subdirectory."""
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    return db_path.parent / "migrations" / f"pre-migration-{stamp}.jsonl"


def _dump_rows_to_jsonl(
    conn: duckdb.DuckDBPyConnection,
    tables: list[str],
    dump_path: Path,
) -> dict[str, int]:
    """Write every row from every table to a JSONL audit file.

    One row per line, including a `_table` discriminator. Non-JSON-native
    types (UUID, datetime, Decimal) are stringified via `default=str`.
    Returns a per-table row count.
    """
    dump_path.parent.mkdir(parents=True, exist_ok=True)
    per_table: dict[str, int] = {}
    with dump_path.open("w", encoding="utf-8") as fh:
        for table in tables:
            _, rows = _read_table_rows(conn, table)
            per_table[table] = len(rows)
            for row in rows:
                record = {"_table": table, **row}
                fh.write(json.dumps(record, default=str) + "\n")
    return per_table


def _replay_rows(
    conn: duckdb.DuckDBPyConnection,
    rows_by_table: dict[str, tuple[list[str], list[dict]]],
    migrations: list[tuple[str, ModuleType]],
) -> tuple[dict[str, int], dict[str, int], dict[str, int]]:
    """Re-insert rows into the freshly-created tables.

    Each row is passed through every discovered migration's
    ``transform(row, table)`` in order before INSERT. A migration
    returning ``None`` skips the row at the transform layer
    (counted in ``transform_skipped``). Rows that survive every
    transform but violate the new schema (e.g. CHECK constraint
    failures) are caught per-row at INSERT time (counted in
    ``insert_skipped``). Both skip loci contribute to the same
    exit-code-2 trigger; see decisions.md 2026-05-15 entry on
    the migrations refactor.

    Returns (preserved, transform_skipped, insert_skipped), each
    keyed by table name.
    """
    preserved: dict[str, int] = {}
    transform_skipped: dict[str, int] = {}
    insert_skipped: dict[str, int] = {}
    for table, (columns, rows) in rows_by_table.items():
        preserved[table] = 0
        transform_skipped[table] = 0
        insert_skipped[table] = 0
        if not rows:
            continue
        placeholders = ", ".join(["?"] * len(columns))
        col_list = ", ".join(columns)
        insert_sql = (
            f"INSERT INTO {table} ({col_list}) VALUES ({placeholders})"
        )
        for row in rows:
            transformed: dict | None = row
            skipped_at_transform = False
            for filename, mig in migrations:
                transformed = mig.transform(transformed, table)
                if transformed is None:
                    transform_skipped[table] += 1
                    print(
                        f"  skipped row in {table} at {filename}",
                        file=sys.stderr,
                    )
                    skipped_at_transform = True
                    break
            if skipped_at_transform:
                continue
            assert transformed is not None  # narrow for type checker
            values = tuple(transformed.get(col) for col in columns)
            try:
                conn.execute(insert_sql, values)
            except duckdb.Error as exc:
                insert_skipped[table] += 1
                print(
                    f"  skipped row in {table}: {type(exc).__name__}",
                    file=sys.stderr,
                )
                continue
            preserved[table] += 1
    return preserved, transform_skipped, insert_skipped


def _migrate_with_preservation(
    conn: duckdb.DuckDBPyConnection,
    db_path: Path,
    migrations: list[tuple[str, ModuleType]],
    yes: bool,
) -> int:
    """Dump → drop → recreate → re-insert through discovered migrations."""
    existing = sorted(_list_application_tables(conn))
    if not existing:
        print("No existing application tables; applying fresh schema.")
        created = _apply_schema_transactional(conn)
        print(f"Schema applied. Created {created} tables.")
        return 0

    # Read every row into memory before touching the schema.
    rows_by_table: dict[str, tuple[list[str], list[dict]]] = {}
    for table in existing:
        rows_by_table[table] = _read_table_rows(conn, table)
    total_rows = sum(len(rows) for _, rows in rows_by_table.values())

    dump_path = _migration_dump_path(db_path)
    _dump_rows_to_jsonl(conn, existing, dump_path)
    print(f"Pre-migration dump: {dump_path}")

    if migrations:
        print(f"Applying {len(migrations)} migration(s):")
        for filename, mig in migrations:
            print(f"  {filename}: {getattr(mig, 'description', '<no description>')}")
    else:
        print("No migrations discovered; rows will be reinserted as-is.")

    if not yes:
        ans = input(
            f"Migrate {total_rows} row(s) across "
            f"{len(existing)} table(s)? [y/N] "
        )
        if ans.strip().lower() != "y":
            print("Aborted.")
            return 1

    # Drop and recreate.
    conn.execute("BEGIN TRANSACTION")
    try:
        for table in existing:
            conn.execute(f"DROP TABLE {table}")
        schema_sql = SCHEMA_PATH.read_text(encoding="utf-8")
        conn.execute(schema_sql)
        conn.execute("COMMIT")
    except Exception:
        conn.execute("ROLLBACK")
        raise

    preserved, transform_skipped, insert_skipped = _replay_rows(
        conn, rows_by_table, migrations
    )

    total_preserved = sum(preserved.values())
    total_transform_skipped = sum(transform_skipped.values())
    total_insert_skipped = sum(insert_skipped.values())
    total_skipped = total_transform_skipped + total_insert_skipped
    print(f"Preserved: {total_preserved} row(s)")
    for table, count in preserved.items():
        print(f"  {table}: {count}")
    if total_skipped:
        print(f"Skipped: {total_skipped} row(s) — review dump")
        if total_transform_skipped:
            print(f"  at transform layer: {total_transform_skipped}")
            for table, count in transform_skipped.items():
                if count:
                    print(f"    {table}: {count}")
        if total_insert_skipped:
            print(f"  at INSERT layer: {total_insert_skipped}")
            for table, count in insert_skipped.items():
                if count:
                    print(f"    {table}: {count}")
        return 2
    return 0


def _migrate_no_preserve(
    conn: duckdb.DuckDBPyConnection, yes: bool
) -> int:
    """Drop all application tables and re-apply the schema. Destructive."""
    existing = sorted(_list_application_tables(conn))
    if existing and not yes:
        ans = input(
            f"DROP {len(existing)} table(s) with all data? [y/N] "
        )
        if ans.strip().lower() != "y":
            print("Aborted.")
            return 1

    conn.execute("BEGIN TRANSACTION")
    try:
        for table in existing:
            conn.execute(f"DROP TABLE {table}")
        schema_sql = SCHEMA_PATH.read_text(encoding="utf-8")
        conn.execute(schema_sql)
        conn.execute("COMMIT")
    except Exception:
        conn.execute("ROLLBACK")
        raise
    print(f"Schema re-applied; {len(existing)} table(s) dropped first.")
    return 0


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
    parser.add_argument(
        "--migrate",
        action="store_true",
        help="Migrate schema. Preserves rows by default; combine with "
             "--no-preserve for a destructive recreate.",
    )
    parser.add_argument(
        "--no-preserve",
        action="store_true",
        help="With --migrate: drop and recreate without preserving rows.",
    )
    parser.add_argument(
        "--yes",
        action="store_true",
        help="Skip confirmation prompts (for unattended runs).",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv if argv is not None else sys.argv[1:])
    db_path = resolve_db_path()
    db_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"DB path: {db_path}")
    expected_tables = set(EXPECTED_SCHEMA)

    with duckdb.connect(str(db_path)) as conn:
        # Migration paths short-circuit the verify-only flow.
        if args.migrate:
            if args.no_preserve:
                return _migrate_no_preserve(conn, yes=args.yes)
            return _migrate_with_preservation(
                conn, db_path, _discover_migrations(), yes=args.yes
            )

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
