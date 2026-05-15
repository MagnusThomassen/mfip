"""SMTP delivery and fallback-queue management for `Alert` payloads.

`send_alert(alert)` renders the alert, sends it via Gmail SMTP, and
writes a delivery-status row to `security_log`. On network failure
the alert JSON is queued under ``runtime/unsent_alerts/`` and the
failure is logged. Every successful send triggers a drain pass over
the queue.

Locked implementation choices (see `decisions.md` 2026-05-15
"mfip_alerts implementation choices"):

- SMTP timeout: 30 seconds (both connect and per-command waits).
- Failure exceptions trigger the fallback queue: SMTPException,
  ConnectionError, OSError, TimeoutError, socket.timeout.
- Queued filename: ``{YYYY-MM-DDTHH-MM-SS-microseconds}_{cid|'system'}.json``
  with NTFS-safe hyphen-for-colon substitution.
- Each drained-retry uses a fresh SMTP connection (avoids per-conn
  rate-limit risk on Gmail).
- Failure ``security_log`` rows do NOT include the SMTP exception
  message text — only the exception class name. Exception messages
  can leak credentials in some failure modes.
"""

from __future__ import annotations

import json
import os
import shutil
import smtplib
import socket
from datetime import UTC, datetime
from email.message import EmailMessage
from pathlib import Path
from uuid import UUID

from dotenv import load_dotenv

from mfip.alerts.models import Alert
from mfip.alerts.renderer import render_alert
from mfip.logging.models import SecurityLogEntry
from mfip.logging.writers import append_security_log

load_dotenv()

SMTP_TIMEOUT_SECONDS = 30

# Severity casing on Alert (Critical/Warning/Advisory) differs from the
# `security_log` table convention (uppercase). Map at the write boundary
# rather than rewriting either model.
_ALERT_TO_LOG_SEVERITY: dict[str, str] = {
    "Critical": "CRITICAL",
    "Warning": "WARNING",
    "Advisory": "ADVISORY",
}

_NETWORK_EXCEPTIONS: tuple[type[BaseException], ...] = (
    smtplib.SMTPException,
    ConnectionError,
    OSError,
    TimeoutError,
    socket.timeout,
)


def _unsent_dir() -> Path:
    """Resolve the fallback queue directory.

    `MFIP_UNSENT_ALERTS_DIR` overrides the default for tests, mirroring
    the `MFIP_DB_PATH` override pattern in `mfip.logging.writers`.
    """
    raw = os.environ.get("MFIP_UNSENT_ALERTS_DIR")
    if raw:
        return Path(raw)
    return Path(r"C:\MFIP\runtime\unsent_alerts")


def _windows_safe_filename(alert: Alert) -> str:
    ts = alert.timestamp.strftime("%Y-%m-%dT%H-%M-%S-%f")
    cid = alert.correlation_id or "system"
    return f"{ts}_{cid}.json"


def _correlation_uuid(alert: Alert) -> UUID | None:
    """Parse alert.correlation_id to UUID; log a warning on malformed input.

    Returns None when correlation_id is missing OR malformed. On malformed
    input also writes a separate Warning `SecurityLogEntry` flagging the
    anomaly so the upstream bug surfaces in the audit trail instead of
    being silently absorbed. The warning write is best-effort — wrapped
    in try/except so a logging failure never blocks alert delivery.
    Encoding follows the `security_log` self-event convention; see
    `decisions.md` 2026-05-15 "security_log self-event encoding".
    """
    if alert.correlation_id is None:
        return None
    try:
        return UUID(alert.correlation_id)
    except ValueError:
        try:
            append_security_log(
                SecurityLogEntry(
                    correlation_id=None,
                    severity="WARNING",
                    issuing_agent="mfip_alerts",
                    issue_description=(
                        "malformed_correlation_id: alert.correlation_id "
                        "was not a valid UUID"
                    ),
                    impact_assessment=json.dumps(
                        {
                            "raw_correlation_id": alert.correlation_id,
                            "alert_title": alert.title,
                            "fallback": "logged as None",
                        },
                        sort_keys=True,
                    ),
                    recommended_action=(
                        "Identify the caller passing malformed "
                        "correlation_id; expected format is UUID hex string"
                    ),
                )
            )
        except Exception:
            # Best-effort: never block alert delivery on warning-write failure.
            pass
        return None


def _log_delivery(
    *,
    alert: Alert,
    log_severity: str,
    issue_description: str,
    details: dict[str, str],
) -> None:
    entry = SecurityLogEntry(
        correlation_id=_correlation_uuid(alert),
        severity=log_severity,  # type: ignore[arg-type]
        issuing_agent="mfip_alerts",
        issue_description=issue_description,
        impact_assessment=json.dumps(details, sort_keys=True),
    )
    append_security_log(entry)


def _read_smtp_config() -> dict[str, str]:
    keys = [
        "MFIP_SMTP_HOST",
        "MFIP_SMTP_PORT",
        "MFIP_SMTP_USER",
        "MFIP_SMTP_APP_PASSWORD",
        "MFIP_ALERT_RECIPIENT",
    ]
    config: dict[str, str] = {}
    missing: list[str] = []
    for key in keys:
        value = os.environ.get(key, "").strip()
        if not value:
            missing.append(key)
        else:
            config[key] = value
    if missing:
        raise RuntimeError(
            f"SMTP config missing required keys: {', '.join(missing)}"
        )
    return config


def _send_via_smtp(message: EmailMessage, config: dict[str, str]) -> None:
    """Open SMTP with timeout, STARTTLS, authenticate, send. Caller wraps
    the network exceptions; this function does not swallow them."""
    message["From"] = config["MFIP_SMTP_USER"]
    message["To"] = config["MFIP_ALERT_RECIPIENT"]
    with smtplib.SMTP(
        config["MFIP_SMTP_HOST"],
        int(config["MFIP_SMTP_PORT"]),
        timeout=SMTP_TIMEOUT_SECONDS,
    ) as smtp:
        smtp.starttls()
        smtp.login(config["MFIP_SMTP_USER"], config["MFIP_SMTP_APP_PASSWORD"])
        smtp.send_message(message)


def _queue_alert(alert: Alert) -> Path:
    queue_dir = _unsent_dir()
    queue_dir.mkdir(parents=True, exist_ok=True)
    path = queue_dir / _windows_safe_filename(alert)
    path.write_text(alert.model_dump_json(indent=2), encoding="utf-8")
    return path


def _move_to_sent(file_path: Path, base_dir: Path) -> Path:
    date_str = datetime.now(UTC).strftime("%Y-%m-%d")
    dest_dir = base_dir / "sent" / date_str
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / file_path.name
    shutil.move(str(file_path), str(dest))
    return dest


def send_alert(alert: Alert) -> bool:
    """Render, send, log delivery status. Returns True on SMTP success.

    On network failure the alert JSON is queued under
    ``runtime/unsent_alerts/`` and a Warning row is written to
    `security_log`. On success an Advisory row is written and
    `drain_unsent_alerts()` runs before returning.
    """
    config = _read_smtp_config()
    message = render_alert(alert)

    try:
        _send_via_smtp(message, config)
    except _NETWORK_EXCEPTIONS as exc:
        _queue_alert(alert)
        _log_delivery(
            alert=alert,
            log_severity="WARNING",
            issue_description=f"alert_delivery_failed: {alert.title}",
            details={
                "title": alert.title,
                "exception_class": type(exc).__name__,
            },
        )
        return False

    _log_delivery(
        alert=alert,
        log_severity="ADVISORY",
        issue_description=f"alert_delivered: {alert.title}",
        details={
            "title": alert.title,
            "recipient": config["MFIP_ALERT_RECIPIENT"],
        },
    )
    drain_unsent_alerts()
    return True


def drain_unsent_alerts() -> dict[str, int]:
    """Retry queued alerts oldest-first. Returns retry counts.

    Each retry uses a fresh SMTP connection — reusing the triggering
    send's connection risks Gmail's per-connection rate limits.
    Successful retries move the JSON file to
    ``unsent_alerts/sent/{YYYY-MM-DD}/``; failures leave the file in
    place for a later drain.
    """
    counts = {"retried": 0, "succeeded": 0, "failed": 0}
    queue_dir = _unsent_dir()
    if not queue_dir.exists():
        return counts

    queued = sorted(
        p
        for p in queue_dir.iterdir()
        if p.is_file() and p.suffix == ".json"
    )
    if not queued:
        return counts

    try:
        config = _read_smtp_config()
    except RuntimeError:
        return counts

    for path in queued:
        counts["retried"] += 1
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
            alert = Alert.model_validate(payload)
        except (json.JSONDecodeError, ValueError):
            counts["failed"] += 1
            continue

        try:
            _send_via_smtp(render_alert(alert), config)
        except _NETWORK_EXCEPTIONS:
            counts["failed"] += 1
            continue

        _move_to_sent(path, queue_dir)
        counts["succeeded"] += 1

    return counts
