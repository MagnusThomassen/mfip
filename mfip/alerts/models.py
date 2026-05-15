"""Pydantic model for MFIP Security Council alerts.

One model — `Alert` — captures the self-contained payload that
`render_alert` turns into a multipart MIME email and `send_alert`
delivers via SMTP (with fallback queue on failure).

Severity casing follows the design-doc convention (Critical /
Warning / Advisory). The `security_log` table uses uppercase
(`CRITICAL` / `WARNING` / `ADVISORY`); the sender maps between
them when writing delivery-status rows.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Literal

from pydantic import BaseModel, Field

Severity = Literal["Critical", "Warning", "Advisory"]


class Alert(BaseModel):
    """Self-contained alert payload.

    The alert body alone must be enough to debug — do not link to
    logs or the dashboard as a substitute for content. `dashboard_link`
    is a forward-compatibility hook for Phase 6 deep-linking; callers
    pass None until then.
    """

    correlation_id: str | None = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    severity: Severity
    issuing_agent: str
    title: str
    summary: str
    error_class: str | None = None
    error_message: str | None = None
    stack_trace: str | None = None
    context_fields: dict[str, str] = Field(default_factory=dict)
    recommended_action: str
    dashboard_link: str | None = None
