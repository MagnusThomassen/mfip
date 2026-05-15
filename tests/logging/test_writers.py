"""Round-trip tests for mfip.logging.writers and the DuckDB schema.

Each test runs against a fresh temp DB initialised from
`mfip/logging/schema.sql`. MFIP_DB_PATH is monkeypatched so the
writers find the temp DB; the schema is initialised via a subprocess
running `scripts/init_db.py` so the fixture exercises the same code
path operators use at install time.

Seven tests cover:
1. decision_log write/read round-trip + payload re-hydration.
2. security_log round-trip across all three severities.
3. severity CHECK constraint rejects invalid values at the DB layer.
4. Append-only API surface: no update/delete export in writers module.
5. Correlation-ID threading through context.new_correlation_id().
6. security_log correlation_id nullability — both bound and None.
7. Cross-log JOIN on correlation_id (the column-add's primary value).
"""

from __future__ import annotations

import os
import subprocess
import sys
from decimal import Decimal
from pathlib import Path
from uuid import UUID, uuid4

import duckdb
import pytest

from mfip.logging import writers
from mfip.logging.models import (
    DecisionLogEntry,
    PlaceholderPayload,
    SecurityLogEntry,
)
from mfip.logging.writers import (
    append_security_log,
    read_decisions_by_correlation,
    read_security_log_by_correlation,
    read_security_log_by_severity,
    write_decision,
)
from mfip.pipeline.context import (
    get_correlation_id,
    new_correlation_id,
    reset_correlation_id,
    set_correlation_id,
)

REPO_ROOT = Path(__file__).resolve().parent.parent.parent


@pytest.fixture
def temp_db(tmp_path, monkeypatch):
    """Fresh temp DB initialised by running `scripts/init_db.py` as a
    subprocess. Uses sys.executable so the subprocess always picks up the
    same interpreter that pytest is running under (the venv python),
    regardless of whether the venv has been activated in the parent
    shell."""
    db_file = tmp_path / "test_mfip.duckdb"
    monkeypatch.setenv("MFIP_DB_PATH", str(db_file))
    subprocess.run(
        [sys.executable, str(REPO_ROOT / "scripts" / "init_db.py")],
        check=True,
        cwd=str(REPO_ROOT),
        env=os.environ.copy(),
    )
    yield db_file


def test_decision_log_round_trip(temp_db):
    cid = uuid4()
    entry = DecisionLogEntry(
        correlation_id=cid,
        agent="extractor_a",
        decision_type="extraction_complete",
        phase="extraction",
        ticker="EQNR",
        confidence_score=Decimal("0.875"),
        payload=PlaceholderPayload(note="round-trip"),
    )
    write_decision(entry)

    rows = read_decisions_by_correlation(cid)
    assert len(rows) == 1
    row = rows[0]
    assert row["agent"] == "extractor_a"
    assert row["decision_type"] == "extraction_complete"
    assert row["phase"] == "extraction"
    assert row["ticker"] == "EQNR"
    assert Decimal(str(row["confidence_score"])) == Decimal("0.875")
    # DuckDB returns UUID column as a uuid.UUID; coerce for comparison.
    assert UUID(str(row["correlation_id"])) == cid

    # Payload re-hydrates through the originating model.
    rehydrated = PlaceholderPayload.model_validate_json(row["payload"])
    assert rehydrated.note == "round-trip"


def test_security_log_round_trip_all_severities(temp_db):
    for severity in ("Advisory", "Warning", "Critical"):
        append_security_log(
            SecurityLogEntry(
                severity=severity,
                issuing_agent="security_council",
                issue_description=f"{severity} test entry",
            )
        )

    for severity in ("Advisory", "Warning", "Critical"):
        rows = read_security_log_by_severity(severity)
        assert len(rows) == 1, f"expected 1 row at {severity}, got {len(rows)}"
        assert rows[0]["severity"] == severity
        assert rows[0]["issuing_agent"] == "security_council"
        assert rows[0]["issue_description"] == f"{severity} test entry"


def test_severity_check_constraint_rejects_invalid(temp_db):
    """Secondary defence: the DB-level CHECK rejects invalid severity
    even if a caller bypasses the Pydantic Literal. Primary defence is
    `SecurityLogEntry.severity: Severity` (Pydantic Literal)."""
    with duckdb.connect(str(temp_db)) as conn:
        with pytest.raises(duckdb.ConstraintException):
            conn.execute(
                """
                INSERT INTO security_log
                    (log_id, severity, issuing_agent, issue_description)
                VALUES (?, ?, ?, ?)
                """,
                (str(uuid4()), "INVALID", "x", "y"),
            )


def test_writers_module_has_no_update_or_delete():
    """The append-only contract for security_log is enforced by the
    absence of update/delete functions in the writers module. This
    test trips any future refactor that quietly adds one."""
    assert not hasattr(writers, "update_security_log")
    assert not hasattr(writers, "delete_security_log")
    # Belt-and-braces: any function whose name starts with these verbs
    # is also a red flag for security_log mutation.
    forbidden_prefixes = ("update_security", "delete_security", "modify_security")
    leaked = [
        name
        for name in dir(writers)
        if any(name.startswith(p) for p in forbidden_prefixes)
    ]
    assert not leaked, f"writers exports forbidden mutation API: {leaked}"


def test_correlation_id_threading_via_context(temp_db):
    """Bind a correlation ID via the context module, write three entries
    through `write_decision` (each constructed with
    `correlation_id=get_correlation_id()`), confirm all three return on
    read."""
    token = set_correlation_id(uuid4())  # ensure isolation from outer state
    try:
        cid = new_correlation_id()
        for i in range(3):
            write_decision(
                DecisionLogEntry(
                    correlation_id=get_correlation_id(),
                    agent=f"agent_{i}",
                    decision_type="t",
                    phase="extraction",
                    payload=PlaceholderPayload(note=f"entry-{i}"),
                )
            )
        rows = read_decisions_by_correlation(cid)
        assert len(rows) == 3
        assert {row["agent"] for row in rows} == {"agent_0", "agent_1", "agent_2"}
    finally:
        reset_correlation_id(token)


def test_security_log_correlation_id_both_cases(temp_db):
    """(a) Bound correlation ID round-trips through
    `read_security_log_by_correlation`. (b) None persists as SQL NULL
    and is reachable via severity lookup but invisible to correlation
    lookup."""
    cid = uuid4()
    bound_token = set_correlation_id(cid)
    try:
        # (a) Pipeline-triggered alert carries the ID.
        append_security_log(
            SecurityLogEntry(
                correlation_id=get_correlation_id(),
                severity="Warning",
                issuing_agent="security_council",
                issue_description="alert with correlation",
            )
        )

        # (b) System-level event with no pipeline context.
        append_security_log(
            SecurityLogEntry(
                correlation_id=None,
                severity="Advisory",
                issuing_agent="system",
                issue_description="startup event",
            )
        )

        # (a) lookup by correlation returns the bound row only.
        by_corr = read_security_log_by_correlation(cid)
        assert len(by_corr) == 1
        assert by_corr[0]["issue_description"] == "alert with correlation"
        assert UUID(str(by_corr[0]["correlation_id"])) == cid

        # (b) NULL row is reachable via severity lookup …
        advisories = read_security_log_by_severity("Advisory")
        assert len(advisories) == 1
        assert advisories[0]["issue_description"] == "startup event"
        assert advisories[0]["correlation_id"] is None

        # … and is NOT returned by a correlation lookup for any UUID,
        # including the one bound to (a).
        bound_only = read_security_log_by_correlation(cid)
        assert all(
            row["issue_description"] != "startup event" for row in bound_only
        )
    finally:
        reset_correlation_id(bound_token)


def test_cross_log_join_on_correlation_id(temp_db):
    """The reason `correlation_id` was added to `security_log`: a
    one-line JOIN finds every log entry from the run that fired an
    alert. This test proves the column-add delivers that value."""
    token = set_correlation_id(uuid4())
    try:
        cid = new_correlation_id()

        write_decision(
            DecisionLogEntry(
                correlation_id=cid,
                agent="extractor_a",
                decision_type="extraction_complete",
                phase="extraction",
                payload=PlaceholderPayload(note="ran ok"),
            )
        )
        append_security_log(
            SecurityLogEntry(
                correlation_id=cid,
                severity="Critical",
                issuing_agent="security_council",
                issue_description="extractor mismatch",
            )
        )

        with duckdb.connect(str(temp_db)) as conn:
            joined = conn.execute(
                """
                SELECT d.agent, s.severity, s.issue_description
                FROM decision_log d
                JOIN security_log s ON d.correlation_id = s.correlation_id
                WHERE s.severity = 'Critical'
                """
            ).fetchall()

        assert len(joined) == 1
        assert joined[0] == ("extractor_a", "Critical", "extractor mismatch")
    finally:
        reset_correlation_id(token)
