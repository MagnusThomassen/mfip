"""Tests for scripts/scheduled_tasks/nightly_log_export.py.

The script imports with a sys.path tweak so we load it via
importlib.util by absolute file path. Module-level constants
(DB_PATH, STATE_FILE, WORKTREE_PATH, EXPORTS_DIR) are
monkeypatched per-test to point at tmp_path.

All Git subprocess calls are mocked — the live exercise (PR
step 10) is where the real Git path runs. Tests verify the
script's contract: cursor advances on JSON write, self-event
rows under the correct event types, atomic state-file writes.
"""

from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
import uuid
from datetime import UTC, datetime
from pathlib import Path

import duckdb
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SCRIPT_PATH = REPO_ROOT / "scripts" / "scheduled_tasks" / "nightly_log_export.py"


def _load_script_module(monkeypatch, db_path: Path, state_file: Path,
                        worktree_path: Path):
    """Load nightly_log_export.py as a module with constants
    monkeypatched to point at tmp_path locations.

    MFIP_DB_PATH is set BEFORE module load so the script's
    setdefault and writers' env-var lookup both resolve to db_path.
    """
    monkeypatch.setenv("MFIP_DB_PATH", str(db_path))
    spec = importlib.util.spec_from_file_location(
        "_test_nightly_log_export", SCRIPT_PATH
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["_test_nightly_log_export"] = module
    spec.loader.exec_module(module)
    monkeypatch.setattr(module, "DB_PATH", db_path)
    monkeypatch.setattr(module, "STATE_FILE", state_file)
    monkeypatch.setattr(module, "WORKTREE_PATH", worktree_path)
    monkeypatch.setattr(module, "EXPORTS_DIR", worktree_path / "exports")
    return module


@pytest.fixture
def script_env(tmp_path, monkeypatch):
    """Provide a fully-isolated script environment.

    Creates: a fresh temp DB initialised from schema.sql, a
    state file path (not yet written), a fake worktree path
    with a .git marker file. Returns the loaded script module.
    """
    db_path = tmp_path / "mfip.duckdb"
    state_file = tmp_path / "export_state.json"
    worktree_path = tmp_path / "logs-archive-worktree"
    worktree_path.mkdir()
    # A real git worktree has .git as a file pointing at the gitdir;
    # script just checks Path(.../.git).exists() which works either way.
    (worktree_path / ".git").write_text("gitdir: /fake\n", encoding="utf-8")

    # Apply schema to the temp DB by running the canonical init script,
    # mirroring how tests/logging/test_writers.py does it.
    monkeypatch.setenv("MFIP_DB_PATH", str(db_path))
    subprocess.run(
        [sys.executable, str(REPO_ROOT / "scripts" / "init_db.py")],
        check=True,
        cwd=str(REPO_ROOT),
        env=os.environ.copy(),
    )

    module = _load_script_module(
        monkeypatch, db_path, state_file, worktree_path
    )
    return module, db_path, state_file, worktree_path


def _insert_security_log_rows(db_path: Path, n: int) -> None:
    """Insert n security_log rows directly via DuckDB. Severity
    cycles through Advisory/Warning/Critical to exercise variation."""
    severities = ["Advisory", "Warning", "Critical"]
    with duckdb.connect(str(db_path)) as con:
        for i in range(n):
            con.execute(
                """
                INSERT INTO security_log
                    (log_id, severity, issuing_agent, issue_description)
                VALUES (?, ?, ?, ?)
                """,
                (
                    str(uuid.uuid4()),
                    severities[i % 3],
                    "test_agent",
                    f"row {i}",
                ),
            )


# --- Cursor state file ---


def test_load_cursor_state_first_run_returns_zeros(script_env):
    module, _, _, _ = script_env
    state = module._load_cursor_state()
    assert state == {"decision_log": 0, "security_log": 0}


def test_cursor_state_round_trip(script_env):
    module, _, state_file, _ = script_env
    written = {
        "decision_log": 7,
        "security_log": 42,
        "last_export_started_utc": "2026-05-15T01:00:00+00:00",
        "last_export_completed_utc": "2026-05-15T01:00:01+00:00",
    }
    module._write_cursor_state(written)
    read_back = module._load_cursor_state()
    assert read_back["decision_log"] == 7
    assert read_back["security_log"] == 42
    assert read_back["last_export_started_utc"] == "2026-05-15T01:00:00+00:00"
    assert read_back["last_export_completed_utc"] == "2026-05-15T01:00:01+00:00"
    # Atomic write must not leave behind a .tmp sibling.
    tmp_sibling = state_file.with_suffix(state_file.suffix + ".tmp")
    assert not tmp_sibling.exists()


# --- Row selection ---


def test_query_new_rows_respects_cursor(script_env):
    module, db_path, _, _ = script_env
    _insert_security_log_rows(db_path, 5)
    with duckdb.connect(str(db_path), read_only=True) as con:
        rows = module._query_new_rows(con, "security_log", cursor=2)
    seqs = [int(r["row_seq"]) for r in rows]
    assert seqs == [3, 4, 5]


def test_query_new_rows_returns_empty_when_caught_up(script_env):
    module, db_path, _, _ = script_env
    _insert_security_log_rows(db_path, 3)
    with duckdb.connect(str(db_path), read_only=True) as con:
        rows = module._query_new_rows(con, "security_log", cursor=3)
    assert rows == []


# --- Self-event paths ---


def test_self_event_written_on_zero_new_rows(script_env, monkeypatch):
    module, db_path, state_file, _ = script_env
    monkeypatch.setattr(module.subprocess, "run", _fail_if_called)

    rc = module.main()

    assert rc == 0
    # State file must NOT be written (skip path doesn't touch state).
    assert not state_file.exists()
    with duckdb.connect(str(db_path), read_only=True) as con:
        rows = con.execute(
            "SELECT severity, issue_description, recommended_action "
            "FROM security_log "
            "WHERE issue_description LIKE 'nightly_log_export_%'"
        ).fetchall()
    assert len(rows) == 1
    severity, issue_desc, rec_action = rows[0]
    assert severity == "Advisory"
    assert issue_desc.startswith("nightly_log_export_skipped_no_new_rows:")
    assert rec_action is None


def test_self_event_written_on_commit_failure(script_env, monkeypatch):
    """Per D3 step 9: JSON + state succeeded, commit failed.
    Cursor IS advanced; JSON file IS on disk; commit_failed self-event."""
    module, db_path, state_file, worktree_path = script_env
    _insert_security_log_rows(db_path, 2)

    real_run = subprocess.run

    def fake_run(cmd, *args, **kwargs):
        # Allow init_db's schema-application subprocess (different cwd
        # signature would break here, but the fixture already finished
        # init by this point). Differentiate by the first arg being a list
        # whose first element is "git" — we want to fail git commit.
        if isinstance(cmd, list) and cmd and cmd[0] == "git":
            if len(cmd) >= 2 and cmd[1] == "commit":
                raise subprocess.CalledProcessError(1, cmd, "fake commit fail")
            # git add and git diff succeed silently
            if cmd[1] == "diff":
                # Simulate one staged file so files_committed > 0
                return subprocess.CompletedProcess(
                    cmd, 0, stdout="exports/2026-05-15.json\n", stderr=""
                )
            return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")
        return real_run(cmd, *args, **kwargs)

    monkeypatch.setattr(module.subprocess, "run", fake_run)

    rc = module.main()
    assert rc == 1

    # State file IS written (cursor advanced on JSON write).
    assert state_file.exists()
    state = json.loads(state_file.read_text(encoding="utf-8"))
    assert state["security_log"] == 2

    # JSON file IS on disk.
    json_files = list((worktree_path / "exports").glob("*.json"))
    assert len(json_files) == 1

    # Self-event row is commit_failed.
    with duckdb.connect(str(db_path), read_only=True) as con:
        rows = con.execute(
            "SELECT severity, issue_description, recommended_action "
            "FROM security_log "
            "WHERE issue_description LIKE 'nightly_log_export_%' "
            "ORDER BY row_seq DESC LIMIT 1"
        ).fetchall()
    severity, issue_desc, rec_action = rows[0]
    assert severity == "Warning"
    assert issue_desc.startswith("nightly_log_export_commit_failed:")
    assert rec_action is not None
    assert "next run will catch up" in rec_action


def test_self_event_written_on_export_failure(script_env, monkeypatch):
    """Per D3 step 10: JSON write fails. State NOT updated, JSON NOT on
    disk, failed self-event."""
    module, db_path, state_file, worktree_path = script_env
    _insert_security_log_rows(db_path, 1)

    def boom(payload, date_str):
        raise OSError("simulated disk failure")

    monkeypatch.setattr(module, "_write_export_json", boom)
    monkeypatch.setattr(module.subprocess, "run", _fail_if_called)

    rc = module.main()
    assert rc == 1

    # State file NOT written.
    assert not state_file.exists()
    # JSON file NOT on disk.
    assert not list((worktree_path / "exports").glob("*.json"))

    with duckdb.connect(str(db_path), read_only=True) as con:
        rows = con.execute(
            "SELECT severity, issue_description, recommended_action "
            "FROM security_log "
            "WHERE issue_description LIKE 'nightly_log_export_%' "
            "ORDER BY row_seq DESC LIMIT 1"
        ).fetchall()
    severity, issue_desc, rec_action = rows[0]
    assert severity == "Warning"
    assert issue_desc.startswith("nightly_log_export_failed:")
    assert "manual re-run required" in rec_action


# --- JSON serialisation ---


def test_json_serialisation_round_trip(script_env):
    """Build a payload with UUIDs and timestamps, write via the
    script's writer, parse back, assert values round-trip cleanly."""
    module, _, _, worktree_path = script_env
    log_id = uuid.uuid4()
    cid = uuid.uuid4()
    now = datetime.now(UTC)
    rows_by_table = {
        "decision_log": [],
        "security_log": [
            {
                "row_seq": 1,
                "log_id": log_id,
                "correlation_id": cid,
                "timestamp": now,
                "severity": "Advisory",
                "issuing_agent": "test",
                "issue_description": "round-trip probe",
            }
        ],
    }
    cursor_before = {"decision_log": 0, "security_log": 0}
    cursor_after = {"decision_log": 0, "security_log": 1}
    payload = module._build_payload(
        rows_by_table, cursor_before, cursor_after, now
    )
    out_path = module._write_export_json(payload, "2026-05-16")

    parsed = json.loads(out_path.read_text(encoding="utf-8"))
    assert parsed["export_metadata"]["row_counts"]["security_log"] == 1
    assert parsed["export_metadata"]["cursor_after"]["security_log"] == 1
    sec_row = parsed["security_log"][0]
    assert sec_row["row_seq"] == 1
    assert sec_row["log_id"] == str(log_id)
    assert sec_row["correlation_id"] == str(cid)
    # Timestamp serialised via str() — non-empty ISO-ish string.
    assert isinstance(sec_row["timestamp"], str) and sec_row["timestamp"]


def _fail_if_called(*args, **kwargs):
    raise AssertionError(
        f"subprocess.run unexpectedly called with: args={args!r} kwargs={kwargs!r}"
    )
