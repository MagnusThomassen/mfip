"""DuckDB writers for MFIP log entries.

Two asymmetric writers:

- `write_decision` — appends to `decision_log`. No-update is convention-only;
  no enforcement function exists, just the absence of one.
- `append_security_log` — appends to `security_log`. No-update is enforced
  by the module API: no `update_security_log` / `delete_security_log`
  function is exported. See CLAUDE.md rule 3.

Writers do not implicitly fetch `correlation_id` from
`mfip.pipeline.context`. Callers construct the entry with
`correlation_id=get_correlation_id()` themselves — keeps the writers
pure and easy to test.

Readers in this module exist for tests and ad-hoc debugging; they are
not part of the agent-facing API.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import duckdb

from mfip.logging.models import DecisionLogEntry, SecurityLogEntry

DEFAULT_DB_PATH = Path(r"C:\MFIP\runtime\mfip.duckdb")


def _db_path() -> Path:
    return Path(os.environ.get("MFIP_DB_PATH", str(DEFAULT_DB_PATH)))


def _connect() -> duckdb.DuckDBPyConnection:
    return duckdb.connect(str(_db_path()))


def _rows_to_dicts(cursor: duckdb.DuckDBPyConnection) -> list[dict[str, Any]]:
    """Convert the cursor's last result into a list of dicts using its
    description metadata. DuckDB's fetchall() returns tuples by default."""
    rows = cursor.fetchall()
    columns = [col[0] for col in cursor.description]
    return [dict(zip(columns, row)) for row in rows]


def write_decision(entry: DecisionLogEntry) -> None:
    """Append a row to `decision_log`. Convention-only no-update."""
    row = entry.to_db_row()
    with _connect() as conn:
        conn.execute(
            """
            INSERT INTO decision_log
                (id, correlation_id, timestamp, agent, decision_type,
                 phase, ticker, confidence_score, payload)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                row["id"],
                row["correlation_id"],
                row["timestamp"],
                row["agent"],
                row["decision_type"],
                row["phase"],
                row["ticker"],
                row["confidence_score"],
                row["payload"],
            ),
        )


def append_security_log(entry: SecurityLogEntry) -> None:
    """Append a row to `security_log`. Append-only by design — no update or
    delete function exists in this module."""
    row = entry.to_db_row()
    correlation_id = row["correlation_id"]
    with _connect() as conn:
        conn.execute(
            """
            INSERT INTO security_log
                (log_id, correlation_id, timestamp, severity, issuing_agent,
                 flagging_officer, issue_description, impact_assessment,
                 recommended_action, pipeline_status, resolved_at,
                 resolution_note)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                str(row["log_id"]),
                str(correlation_id) if correlation_id is not None else None,
                row["timestamp"],
                row["severity"],
                row["issuing_agent"],
                row["flagging_officer"],
                row["issue_description"],
                row["impact_assessment"],
                row["recommended_action"],
                row["pipeline_status"],
                row["resolved_at"],
                row["resolution_note"],
            ),
        )


def read_decisions_by_correlation(correlation_id) -> list[dict[str, Any]]:
    with _connect() as conn:
        cur = conn.execute(
            "SELECT * FROM decision_log WHERE correlation_id = ? ORDER BY timestamp",
            (str(correlation_id),),
        )
        return _rows_to_dicts(cur)


def read_security_log_by_severity(severity: str) -> list[dict[str, Any]]:
    with _connect() as conn:
        cur = conn.execute(
            "SELECT * FROM security_log WHERE severity = ? ORDER BY timestamp DESC",
            (severity,),
        )
        return _rows_to_dicts(cur)


def read_security_log_by_correlation(correlation_id) -> list[dict[str, Any]]:
    with _connect() as conn:
        cur = conn.execute(
            "SELECT * FROM security_log WHERE correlation_id = ? ORDER BY timestamp",
            (str(correlation_id),),
        )
        return _rows_to_dicts(cur)
