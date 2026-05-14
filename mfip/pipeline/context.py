"""Pipeline correlation ID infrastructure.

Module-level `contextvars.ContextVar` carrying the correlation ID for
the current pipeline run. Threads through every log entry written by
agents under that run so audit-trail queries can join `decision_log`
and `security_log` rows back to one origin.

Per 2026-05-14 PR-A decision: use `ContextVar`, not a `PipelineContext`
parameter threaded through every call. Async-safe by construction, no
dependency cost, doesn't pollute agent signatures.
"""

from __future__ import annotations

import contextvars
from uuid import UUID, uuid4

# Module-level ContextVar. None default = "not inside a pipeline run".
_correlation_id: contextvars.ContextVar[UUID | None] = contextvars.ContextVar(
    "mfip_correlation_id", default=None
)


def new_correlation_id() -> UUID:
    """Mint a new correlation ID and bind it to the current context.

    Called once at pipeline entry (when the user kicks off "analyse <ticker>").
    Returns the ID so the caller can also log/display it.
    """
    cid = uuid4()
    _correlation_id.set(cid)
    return cid


def get_correlation_id() -> UUID:
    """Return the current correlation ID.

    Raises RuntimeError if called outside a pipeline run. Writers must call
    this — refusing to default to a fresh UUID is intentional, since silently
    writing log entries with orphan correlation IDs would defeat the audit
    chain.
    """
    cid = _correlation_id.get()
    if cid is None:
        raise RuntimeError(
            "No correlation ID bound. Call new_correlation_id() at pipeline "
            "entry before any log write."
        )
    return cid


def set_correlation_id(cid: UUID) -> contextvars.Token:
    """Bind an existing correlation ID to the current context.

    Returns the Token so the caller can reset() the context afterwards.
    Useful in tests, and in any scenario where the ID is reconstructed
    from an external source (e.g. resuming a paused pipeline).
    """
    return _correlation_id.set(cid)


def reset_correlation_id(token: contextvars.Token) -> None:
    """Reset the context to its prior state. Pair with set_correlation_id()."""
    _correlation_id.reset(token)
