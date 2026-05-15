"""
Nightly log export — exports new decision_log and security_log
rows to JSON and commits to the logs-archive Git branch.

Triggered by Windows Task Scheduler at 02:00 local time. May
also be invoked manually for testing.

One-time setup (operator runs once):
    cd C:\\MFIP\\repo
    git worktree add C:\\MFIP\\repo-logs-archive logs-archive

The script writes JSON to the worktree at
``C:\\MFIP\\repo-logs-archive\\exports\\<YYYY-MM-DD>.json``,
commits it on the ``logs-archive`` branch, and pushes.

Cursor state lives at ``C:\\MFIP\\runtime\\export_state.json``
and advances on JSON write success (not on commit success):
if the JSON file lands but git push fails, the next run picks
up the uncommitted file via ``git add exports/*.json`` and
catches up automatically.

Filename uses local date (Norwegian time) so operators can
match files to calendar days they remember; the export's UTC
timestamp is preserved in ``export_metadata.exported_at_utc``
inside the JSON.

See ``decisions.md`` 2026-05-15 entry "PR-C nightly log
export contract" for full design rationale.
"""

from __future__ import annotations

import datetime as dt
import json
import os
import subprocess
import sys
import traceback
import uuid
from pathlib import Path
from typing import Any

import duckdb

# Constants
DB_PATH = Path(os.environ.get("MFIP_DB_PATH", r"C:\MFIP\runtime\mfip.duckdb"))
STATE_FILE = Path(r"C:\MFIP\runtime\export_state.json")
WORKTREE_PATH = Path(r"C:\MFIP\repo-logs-archive")
EXPORTS_DIR = WORKTREE_PATH / "exports"
LOG_TABLES = ("decision_log", "security_log")

# Resolve DB path into env var so mfip.logging.writers' _db_path()
# resolves to the same location as DB_PATH. setdefault preserves
# any externally-set value (test fixtures, operator dev runs).
os.environ.setdefault("MFIP_DB_PATH", str(DB_PATH))

# Imports from mfip.* — script needs sys.path manipulation since
# scripts/ goes on path, not repo root. Same shape as other scripts.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from mfip.logging.models import SecurityLogEntry  # noqa: E402
from mfip.logging.writers import append_security_log  # noqa: E402


def _load_cursor_state() -> dict[str, Any]:
    """Load cursor state file, or return defaults for first run."""
    if not STATE_FILE.exists():
        return {tbl: 0 for tbl in LOG_TABLES}
    with STATE_FILE.open("r", encoding="utf-8") as f:
        state = json.load(f)
    for tbl in LOG_TABLES:
        state.setdefault(tbl, 0)
    return state


def _write_cursor_state(state: dict[str, Any]) -> None:
    """Atomic write of cursor state file via temp + os.replace."""
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    tmp = STATE_FILE.with_suffix(STATE_FILE.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8") as f:
        json.dump(state, f, indent=2, sort_keys=True, default=str)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, STATE_FILE)


def _query_new_rows(
    con: duckdb.DuckDBPyConnection, table: str, cursor: int
) -> list[dict[str, Any]]:
    """Return rows with row_seq > cursor, ordered by row_seq ASC."""
    cols = [
        r[0]
        for r in con.execute(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_name = ? ORDER BY ordinal_position",
            [table],
        ).fetchall()
    ]
    rows = con.execute(
        f"SELECT * FROM {table} WHERE row_seq > ? ORDER BY row_seq ASC",
        [cursor],
    ).fetchall()
    return [dict(zip(cols, r)) for r in rows]


def _max_row_seq(rows: list[dict[str, Any]], fallback: int) -> int:
    """Return the maximum row_seq from rows, or fallback if empty."""
    if not rows:
        return fallback
    return max(int(r["row_seq"]) for r in rows)


def _write_self_event(
    event_type: str,
    severity: str,
    description: str,
    details: dict[str, Any],
    recommended_action: str | None = None,
) -> None:
    """Write a security_log self-event row per the convention in
    decisions.md 2026-05-15 (event_type as issue_description prefix,
    JSON details in impact_assessment)."""
    entry = SecurityLogEntry(
        log_id=uuid.uuid4(),
        correlation_id=None,
        issuing_agent="nightly_log_export",
        severity=severity,
        issue_description=f"{event_type}: {description}",
        impact_assessment=json.dumps(details, sort_keys=True, default=str),
        recommended_action=recommended_action,
    )
    append_security_log(entry)


def _build_payload(
    rows_by_table: dict[str, list[dict[str, Any]]],
    cursor_before: dict[str, int],
    cursor_after: dict[str, int],
    started_utc: dt.datetime,
) -> dict[str, Any]:
    """Build the JSON-serialisable export payload per D4."""
    return {
        "export_metadata": {
            "exported_at_utc": started_utc.isoformat(),
            "cursor_before": {
                tbl: cursor_before[tbl] for tbl in LOG_TABLES
            },
            "cursor_after": {
                tbl: cursor_after[tbl] for tbl in LOG_TABLES
            },
            "row_counts": {
                tbl: len(rows_by_table[tbl]) for tbl in LOG_TABLES
            },
        },
        "decision_log": rows_by_table["decision_log"],
        "security_log": rows_by_table["security_log"],
    }


def _write_export_json(payload: dict[str, Any], date_str: str) -> Path:
    """Write the export JSON to the worktree's exports/ directory.
    Returns the file path. D4: sort_keys + default=str + indent=2."""
    EXPORTS_DIR.mkdir(parents=True, exist_ok=True)
    out_path = EXPORTS_DIR / f"{date_str}.json"
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, sort_keys=True, default=str)
    return out_path


def _row_seq_range(rows: list[dict[str, Any]]) -> str:
    """Format the 'row_seq X through Y' fragment for the commit message."""
    if not rows:
        return ""
    seqs = [int(r["row_seq"]) for r in rows]
    return f" (row_seq {min(seqs)} through {max(seqs)})"


def _commit_and_push(
    rows_by_table: dict[str, list[dict[str, Any]]],
    date_str: str,
) -> int:
    """Switch to worktree, add+commit+push. Return files_committed.
    Raises subprocess.CalledProcessError on any git failure.

    Per D6: stages all unstaged exports/*.json, so a previous run's
    failed commit gets caught up naturally.
    """
    cwd = str(WORKTREE_PATH)
    subprocess.run(
        ["git", "add", "exports"], cwd=cwd, check=True
    )
    staged = subprocess.run(
        ["git", "diff", "--cached", "--name-only", "--", "exports"],
        cwd=cwd,
        check=True,
        capture_output=True,
        text=True,
    )
    files_committed = sum(
        1 for line in staged.stdout.splitlines() if line.strip()
    )

    msg_lines = [
        f"nightly log export {date_str}",
        f"decision_log: {len(rows_by_table['decision_log'])} rows"
        + _row_seq_range(rows_by_table["decision_log"]),
        f"security_log: {len(rows_by_table['security_log'])} rows"
        + _row_seq_range(rows_by_table["security_log"]),
        f"files_committed: {files_committed}",
    ]
    msg = "\n".join(msg_lines)

    subprocess.run(
        ["git", "commit", "-m", msg], cwd=cwd, check=True
    )
    subprocess.run(
        ["git", "push", "origin", "logs-archive"], cwd=cwd, check=True
    )
    return files_committed


def main() -> int:
    started_utc = dt.datetime.now(dt.timezone.utc)
    local_date_str = dt.datetime.now().strftime("%Y-%m-%d")
    cursor_before = _load_cursor_state()

    # Verify worktree exists. A worktree's .git is a file, not a directory;
    # Path.exists() handles both via stat() so the check works for either.
    if not WORKTREE_PATH.exists() or not (WORKTREE_PATH / ".git").exists():
        _write_self_event(
            "nightly_log_export_failed",
            "Warning",
            f"logs-archive worktree missing at {WORKTREE_PATH}",
            details={
                "expected_worktree_path": str(WORKTREE_PATH),
                "setup_command": (
                    "git worktree add C:\\MFIP\\repo-logs-archive logs-archive"
                ),
                "cursor_before": cursor_before,
            },
            recommended_action=(
                "Run the one-time worktree setup command and re-run the script."
            ),
        )
        return 2

    try:
        con = duckdb.connect(str(DB_PATH), read_only=True)
        try:
            rows_by_table = {
                tbl: _query_new_rows(con, tbl, int(cursor_before[tbl]))
                for tbl in LOG_TABLES
            }
        finally:
            con.close()

        total_new = sum(len(rows) for rows in rows_by_table.values())
        completed_utc = dt.datetime.now(dt.timezone.utc)

        # Zero-new-rows skip path (D3 step 4).
        if total_new == 0:
            _write_self_event(
                "nightly_log_export_skipped_no_new_rows",
                "Advisory",
                "no new rows since last export",
                details={
                    "cursor_before": cursor_before,
                    "row_counts": {tbl: 0 for tbl in LOG_TABLES},
                    "last_export_started_utc": started_utc.isoformat(),
                    "last_export_completed_utc": completed_utc.isoformat(),
                },
            )
            return 0

        # Compute new cursor values: max(existing cursor, max row_seq seen).
        cursor_after = {
            tbl: _max_row_seq(rows_by_table[tbl], int(cursor_before[tbl]))
            for tbl in LOG_TABLES
        }

        payload = _build_payload(
            rows_by_table, cursor_before, cursor_after, started_utc
        )

        # Write JSON first; if this fails, state file is untouched.
        json_path = _write_export_json(payload, local_date_str)

        # Then advance cursor state. This is the moment cursor advances
        # — JSON write success, not commit success (D3).
        new_state: dict[str, Any] = dict(cursor_after)
        new_state["last_export_started_utc"] = started_utc.isoformat()
        new_state["last_export_completed_utc"] = completed_utc.isoformat()
        _write_cursor_state(new_state)
    except Exception as exc:
        # JSON or state write failed — cursor not advanced.
        _write_self_event(
            "nightly_log_export_failed",
            "Warning",
            f"export failed: {type(exc).__name__}",
            details={
                "exception_class": type(exc).__name__,
                "exception_message": str(exc)[:500],
                "traceback": traceback.format_exc()[-2000:],
                "cursor_before": cursor_before,
            },
            recommended_action=(
                "Investigate DB connectivity and disk space; "
                "manual re-run required."
            ),
        )
        return 1

    # Commit + push.
    try:
        files_committed = _commit_and_push(rows_by_table, local_date_str)
    except Exception as exc:
        _write_self_event(
            "nightly_log_export_commit_failed",
            "Warning",
            f"commit/push failed: {type(exc).__name__}",
            details={
                "exception_class": type(exc).__name__,
                "exception_message": str(exc)[:500],
                "traceback": traceback.format_exc()[-2000:],
                "json_file": str(json_path),
                "cursor_before": cursor_before,
                "cursor_after": cursor_after,
                "row_counts": {
                    tbl: len(rows_by_table[tbl]) for tbl in LOG_TABLES
                },
                "last_export_started_utc": started_utc.isoformat(),
                "last_export_completed_utc": completed_utc.isoformat(),
            },
            recommended_action=(
                "Investigate network or git state; next run will catch up "
                "automatically."
            ),
        )
        return 1

    # Success self-event row.
    _write_self_event(
        "nightly_log_export_succeeded",
        "Advisory",
        f"exported {total_new} row(s)",
        details={
            "json_file": str(json_path),
            "files_committed": files_committed,
            "cursor_before": cursor_before,
            "cursor_after": cursor_after,
            "row_counts": {
                tbl: len(rows_by_table[tbl]) for tbl in LOG_TABLES
            },
            "last_export_started_utc": started_utc.isoformat(),
            "last_export_completed_utc": dt.datetime.now(
                dt.timezone.utc
            ).isoformat(),
        },
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
