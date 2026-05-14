"""Tests for mfip.pipeline.context.

Five cases:
1. new_correlation_id returns a UUID and binds it to the current context.
2. get_correlation_id after new_correlation_id returns the same ID.
3. get_correlation_id with no prior binding raises RuntimeError.
4. set + reset restores prior state (including unbound).
5. Two contextvars.copy_context() runs see independent IDs — proves
   request-scope isolation.
"""

from __future__ import annotations

import contextvars
from uuid import UUID

import pytest

from mfip.pipeline.context import (
    get_correlation_id,
    new_correlation_id,
    reset_correlation_id,
    set_correlation_id,
)


def _run_isolated(fn):
    """Execute `fn` in a fresh copied context so module-level state from
    the outer test does not leak in."""
    return contextvars.copy_context().run(fn)


def test_new_correlation_id_returns_uuid_and_binds():
    def body():
        cid = new_correlation_id()
        assert isinstance(cid, UUID)
        assert get_correlation_id() == cid
        return cid

    _run_isolated(body)


def test_get_after_new_returns_same_id():
    def body():
        cid = new_correlation_id()
        assert get_correlation_id() == cid
        # Two reads should be stable.
        assert get_correlation_id() == cid

    _run_isolated(body)


def test_get_without_binding_raises():
    def body():
        with pytest.raises(RuntimeError, match="No correlation ID bound"):
            get_correlation_id()

    _run_isolated(body)


def test_set_and_reset_restores_prior_state():
    def body():
        # Start unbound.
        with pytest.raises(RuntimeError):
            get_correlation_id()
        # Bind via set.
        cid = UUID("12345678-1234-5678-1234-567812345678")
        token = set_correlation_id(cid)
        assert get_correlation_id() == cid
        # Reset — should return to unbound.
        reset_correlation_id(token)
        with pytest.raises(RuntimeError):
            get_correlation_id()

    _run_isolated(body)


def test_copy_context_isolates_runs():
    """Two contextvars.copy_context() runs each mint their own ID and
    do not see each other's bindings."""
    seen: dict[str, UUID] = {}

    def run_a():
        seen["a"] = new_correlation_id()

    def run_b():
        seen["b"] = new_correlation_id()

    contextvars.copy_context().run(run_a)
    contextvars.copy_context().run(run_b)

    assert seen["a"] != seen["b"]
    # Outer context is unaffected by either run.
    with pytest.raises(RuntimeError):
        get_correlation_id()
