"""Pydantic models for MFIP log entries.

Two top-level entry models — `DecisionLogEntry`, `SecurityLogEntry` —
plus a scaffold for the eventual discriminated union of per-agent
payload types under `decision_log`. Each concrete payload model gets
added to `DecisionPayload` as its owning agent comes online in
Phase 3+.

Schemas: decisions.md 2026-05-14 "decision_log schema" and
2026-05-14 "security_log schema extension".
"""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from typing import Annotated, Literal, Union
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field

Severity = Literal["ADVISORY", "WARNING", "CRITICAL"]
Phase = Literal[
    "extraction",
    "validation",
    "intelligence",
    "modelling",
    "recommendation",
    "portfolio",
]


class PlaceholderPayload(BaseModel):
    """Placeholder for early Phase 2 testing.

    Real per-agent payload models (ExtractionCompletePayload,
    DcfOutputPayload, ChiefRecommendationPayload, etc.) are added in
    the phase that introduces the corresponding agent. Each must be a
    BaseModel subclass and registered in the DecisionPayload union
    below.
    """

    note: str


# TODO(phase3+): switch `DecisionLogEntry.payload` from `BaseModel` to
# `DecisionPayload` and add `Field(discriminator="decision_type")` once a
# second concrete payload type lands. Pydantic discriminated unions need
# at least two members to be meaningful.
DecisionPayload = Annotated[
    Union[PlaceholderPayload],
    Field(discriminator=None),
]


class DecisionLogEntry(BaseModel):
    """One row in `decision_log`. Frozen — never mutate after construction."""

    model_config = ConfigDict(frozen=True)

    id: UUID = Field(default_factory=uuid4)
    correlation_id: UUID
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    agent: str
    decision_type: str
    phase: Phase
    ticker: str | None = None
    confidence_score: Decimal | None = Field(
        default=None, ge=0, le=1, max_digits=4, decimal_places=3
    )
    payload: BaseModel  # See DecisionPayload above; widened until 2+ types exist.

    def to_db_row(self) -> dict:
        """Serialise to a dict matching `decision_log` column order. Payload
        is emitted as a JSON string for the DuckDB JSON column."""
        return {
            "id": str(self.id),
            "correlation_id": str(self.correlation_id),
            "timestamp": self.timestamp,
            "agent": self.agent,
            "decision_type": self.decision_type,
            "phase": self.phase,
            "ticker": self.ticker,
            "confidence_score": self.confidence_score,
            "payload": self.payload.model_dump_json(),
        }


class SecurityLogEntry(BaseModel):
    """One row in `security_log`. Frozen. `correlation_id` nullable for
    system-level events (startup, maintenance, manual operator actions)
    that occur outside any pipeline run."""

    model_config = ConfigDict(frozen=True)

    log_id: UUID = Field(default_factory=uuid4)
    correlation_id: UUID | None = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    severity: Severity
    issuing_agent: str
    flagging_officer: str | None = None
    issue_description: str
    impact_assessment: str | None = None
    recommended_action: str | None = None
    pipeline_status: Literal["RUNNING", "SUSPENDED"] | None = None
    resolved_at: datetime | None = None
    resolution_note: str | None = None

    def to_db_row(self) -> dict:
        return self.model_dump(mode="python")
