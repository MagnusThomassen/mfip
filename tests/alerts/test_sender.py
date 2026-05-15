"""SMTP-mocked tests for `mfip.alerts.sender`.

No live SMTP. Every test patches `mfip.alerts.sender.smtplib.SMTP`
at the import site; the patched object is a `MagicMock` (success
path) or raises an exception (failure path) via `side_effect`.

The temp-DB fixture mirrors `tests/logging/test_writers.py`: a
fresh DuckDB initialised by running `scripts/init_db.py` as a
subprocess under the same interpreter pytest is running.
"""

from __future__ import annotations

import json
import os
import smtplib
import subprocess
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from mfip.alerts import sender as sender_module
from mfip.alerts.models import Alert
from mfip.alerts.sender import drain_unsent_alerts, send_alert
from mfip.logging.writers import (
    read_security_log_by_severity,
)

REPO_ROOT = Path(__file__).resolve().parent.parent.parent


@pytest.fixture
def temp_db(tmp_path, monkeypatch):
    db_file = tmp_path / "test_mfip.duckdb"
    monkeypatch.setenv("MFIP_DB_PATH", str(db_file))
    subprocess.run(
        [sys.executable, str(REPO_ROOT / "scripts" / "init_db.py")],
        check=True,
        cwd=str(REPO_ROOT),
        env=os.environ.copy(),
    )
    return db_file


@pytest.fixture
def smtp_env(monkeypatch):
    """Override SMTP env vars with safe stub values for tests."""
    monkeypatch.setenv("MFIP_SMTP_HOST", "smtp.example.test")
    monkeypatch.setenv("MFIP_SMTP_PORT", "587")
    monkeypatch.setenv("MFIP_SMTP_USER", "sender@example.test")
    monkeypatch.setenv("MFIP_SMTP_APP_PASSWORD", "stub-password-1234")
    monkeypatch.setenv("MFIP_ALERT_RECIPIENT", "recipient@example.test")


@pytest.fixture
def unsent_dir(tmp_path, monkeypatch):
    queue = tmp_path / "unsent_alerts"
    monkeypatch.setenv("MFIP_UNSENT_ALERTS_DIR", str(queue))
    return queue


def _alert(**overrides) -> Alert:
    defaults = dict(
        severity="Critical",
        issuing_agent="security_council",
        title="EOD ingestion failed",
        summary="EQNR EOD did not complete.",
        recommended_action="Re-run ingestion.",
    )
    defaults.update(overrides)
    return Alert(**defaults)


def test_successful_send_writes_advisory_alert_delivered_row(
    temp_db, smtp_env, unsent_dir
):
    with patch("mfip.alerts.sender.smtplib.SMTP") as smtp_cls:
        smtp_cls.return_value.__enter__.return_value = MagicMock()
        result = send_alert(_alert(title="Test delivery"))

    assert result is True
    smtp_cls.assert_called_once()
    # Connection used the locked 30s timeout.
    _, kwargs = smtp_cls.call_args
    assert kwargs.get("timeout") == sender_module.SMTP_TIMEOUT_SECONDS

    rows = read_security_log_by_severity("ADVISORY")
    delivered = [
        r for r in rows
        if r["issuing_agent"] == "mfip_alerts"
        and "alert_delivered" in r["issue_description"]
    ]
    assert len(delivered) == 1
    assert "Test delivery" in delivered[0]["issue_description"]

    # impact_assessment is a JSON-serialised details dict containing
    # the recipient address (locked behaviour — recipient is in env config,
    # not credential-sensitive).
    details = json.loads(delivered[0]["impact_assessment"])
    assert details["title"] == "Test delivery"
    assert details["recipient"] == "recipient@example.test"


def test_smtp_failure_queues_json_and_writes_warning_row(
    temp_db, smtp_env, unsent_dir
):
    with patch("mfip.alerts.sender.smtplib.SMTP") as smtp_cls:
        smtp_cls.return_value.__enter__.side_effect = smtplib.SMTPException(
            "simulated failure"
        )
        result = send_alert(_alert(title="Network down"))

    assert result is False

    # JSON queued to the unsent directory.
    assert unsent_dir.exists()
    queued = list(unsent_dir.glob("*.json"))
    assert len(queued) == 1
    # Windows-safe: no ':' anywhere in filename.
    assert ":" not in queued[0].name

    # Warning row in security_log.
    rows = read_security_log_by_severity("WARNING")
    failures = [
        r for r in rows
        if r["issuing_agent"] == "mfip_alerts"
        and "alert_delivery_failed" in r["issue_description"]
    ]
    assert len(failures) == 1

    # Failure details include the exception class but NOT the message
    # text (locked: SMTP exception messages can leak credentials).
    details = json.loads(failures[0]["impact_assessment"])
    assert details["exception_class"] == "SMTPException"
    assert "simulated failure" not in failures[0]["impact_assessment"]
    assert "simulated failure" not in failures[0]["issue_description"]


def test_send_alert_returns_true_on_success_and_false_on_failure(
    temp_db, smtp_env, unsent_dir
):
    with patch("mfip.alerts.sender.smtplib.SMTP") as smtp_cls:
        smtp_cls.return_value.__enter__.return_value = MagicMock()
        assert send_alert(_alert(title="ok")) is True

    with patch("mfip.alerts.sender.smtplib.SMTP") as smtp_cls:
        smtp_cls.return_value.__enter__.side_effect = ConnectionError("no route")
        assert send_alert(_alert(title="nope")) is False


def test_drain_retries_oldest_first(
    temp_db, smtp_env, unsent_dir
):
    # Pre-seed three queued alerts with distinct timestamps. We bypass
    # send_alert and write directly so the drain path is exercised in
    # isolation.
    unsent_dir.mkdir(parents=True, exist_ok=True)
    base = datetime(2026, 5, 15, 10, 0, 0, tzinfo=UTC)
    titles_by_order = []
    for offset_seconds, title in [
        (0, "first"),
        (60, "second"),
        (120, "third"),
    ]:
        a = _alert(title=title)
        a = a.model_copy(update={"timestamp": base + timedelta(seconds=offset_seconds)})
        filename = sender_module._windows_safe_filename(a)
        (unsent_dir / filename).write_text(a.model_dump_json(indent=2), encoding="utf-8")
        titles_by_order.append(title)

    sent_titles: list[str] = []

    def capture_send(self, message):
        # `message` may carry the rendered Subject; extract the title.
        subject = message["Subject"]
        # Subject format: "[MFIP {severity}] {title}"
        assert subject.startswith("[MFIP ")
        title = subject.split("] ", 1)[1]
        sent_titles.append(title)

    with patch("mfip.alerts.sender.smtplib.SMTP") as smtp_cls:
        smtp_instance = MagicMock()
        smtp_instance.send_message.side_effect = lambda msg: capture_send(
            smtp_instance, msg
        )
        smtp_cls.return_value.__enter__.return_value = smtp_instance

        counts = drain_unsent_alerts()

    assert counts == {"retried": 3, "succeeded": 3, "failed": 0}
    assert sent_titles == titles_by_order


def test_malformed_correlation_id_writes_warning_and_proceeds(
    temp_db, smtp_env, unsent_dir
):
    """A non-UUID `correlation_id` does not block delivery; the alert is
    sent, the delivery-status row stores correlation_id=None, and a
    separate Warning row captures the raw input for upstream debugging."""
    alert = _alert(title="Malformed cid case")
    alert = alert.model_copy(update={"correlation_id": "not-a-uuid-at-all"})

    with patch("mfip.alerts.sender.smtplib.SMTP") as smtp_cls:
        smtp_cls.return_value.__enter__.return_value = MagicMock()
        result = send_alert(alert)

    assert result is True, "alert delivery must not be blocked by malformed cid"

    # Delivery-status row: Advisory, alert_delivered, correlation_id=None.
    advisories = read_security_log_by_severity("ADVISORY")
    delivered = [
        r for r in advisories
        if r["issuing_agent"] == "mfip_alerts"
        and "alert_delivered" in r["issue_description"]
    ]
    assert len(delivered) == 1
    assert delivered[0]["correlation_id"] is None
    assert "Malformed cid case" in delivered[0]["issue_description"]

    # Warning row: malformed_correlation_id, correlation_id=None,
    # impact_assessment JSON contains the raw input.
    warnings_ = read_security_log_by_severity("WARNING")
    malformed = [
        r for r in warnings_
        if r["issuing_agent"] == "mfip_alerts"
        and "malformed_correlation_id" in r["issue_description"]
    ]
    assert len(malformed) == 1
    assert malformed[0]["correlation_id"] is None
    details = json.loads(malformed[0]["impact_assessment"])
    assert details["raw_correlation_id"] == "not-a-uuid-at-all"
    assert details["alert_title"] == "Malformed cid case"
    assert details["fallback"] == "logged as None"


def test_drained_files_moved_to_sent_dated_subdir(
    temp_db, smtp_env, unsent_dir
):
    unsent_dir.mkdir(parents=True, exist_ok=True)
    a = _alert(title="will-be-drained")
    a = a.model_copy(
        update={"timestamp": datetime(2026, 5, 15, 12, 0, 0, tzinfo=UTC)}
    )
    original_filename = sender_module._windows_safe_filename(a)
    original_path = unsent_dir / original_filename
    original_path.write_text(a.model_dump_json(indent=2), encoding="utf-8")

    with patch("mfip.alerts.sender.smtplib.SMTP") as smtp_cls:
        smtp_cls.return_value.__enter__.return_value = MagicMock()
        counts = drain_unsent_alerts()

    assert counts == {"retried": 1, "succeeded": 1, "failed": 0}
    assert not original_path.exists(), "queued file should have been moved"

    today = datetime.now(UTC).strftime("%Y-%m-%d")
    sent_dir = unsent_dir / "sent" / today
    moved = list(sent_dir.glob("*.json"))
    assert len(moved) == 1
    assert moved[0].name == original_filename
