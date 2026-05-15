"""Pydantic model tests for `mfip.alerts.models.Alert`."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from pydantic import ValidationError

from mfip.alerts.models import Alert


def _minimal_alert(**overrides) -> Alert:
    defaults = dict(
        severity="Critical",
        issuing_agent="security_council",
        title="Bloomberg ingestion failure",
        summary="EOD ingestion did not complete for EQNR.",
        recommended_action="Re-run ingestion from the lab notebook.",
    )
    defaults.update(overrides)
    return Alert(**defaults)


def test_alert_constructs_with_required_fields():
    alert = _minimal_alert()

    assert alert.severity == "Critical"
    assert alert.issuing_agent == "security_council"
    assert alert.title == "Bloomberg ingestion failure"
    assert alert.summary == "EOD ingestion did not complete for EQNR."
    assert alert.recommended_action == "Re-run ingestion from the lab notebook."

    # Optional fields default cleanly.
    assert alert.correlation_id is None
    assert alert.error_class is None
    assert alert.error_message is None
    assert alert.stack_trace is None
    assert alert.context_fields == {}
    assert alert.dashboard_link is None


def test_alert_timestamp_defaults_to_aware_utc():
    before = datetime.now(UTC)
    alert = _minimal_alert()
    after = datetime.now(UTC)

    assert alert.timestamp.tzinfo is not None, "timestamp must be timezone-aware"
    # Within a small window of the construction time.
    assert before - timedelta(seconds=1) <= alert.timestamp <= after + timedelta(
        seconds=1
    )


def test_alert_stack_trace_accepts_none_and_long_strings_unchanged():
    # None.
    alert = _minimal_alert(stack_trace=None)
    assert alert.stack_trace is None

    # 500 lines — model does not truncate; truncation lives in the renderer.
    long_trace = "\n".join(f"frame {i}" for i in range(500))
    alert = _minimal_alert(stack_trace=long_trace)
    assert alert.stack_trace == long_trace
    assert len(alert.stack_trace.splitlines()) == 500


def test_alert_severity_rejects_invalid_values():
    with pytest.raises(ValidationError):
        _minimal_alert(severity="Critcal")  # noqa: typo intentional

    with pytest.raises(ValidationError):
        _minimal_alert(severity="critical")  # case-sensitive

    with pytest.raises(ValidationError):
        _minimal_alert(severity="Info")
