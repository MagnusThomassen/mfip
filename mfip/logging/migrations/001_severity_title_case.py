"""
Migration 001 — Normalise severity casing to Title-case across log
tables.

Applied to production DB in PR #49 (Session 16, 2026-05-15).
Idempotent on already-Title-case input (unknown severities fall
through to the DB-INSERT layer where the CHECK constraint catches
them, matching the pre-refactor behaviour).
"""

description = "Normalise severity casing to Title-case across log tables"

_SEVERITY_MAP = {
    "ADVISORY": "Advisory",
    "WARNING": "Warning",
    "CRITICAL": "Critical",
}


def transform(row: dict, table_name: str) -> dict | None:
    """Map row's severity field (if present and UPPER-case) to
    Title-case. Title-case input passes through unchanged.
    Unknown severities are not handled here — they reach the
    INSERT layer where the CHECK constraint rejects them and
    _replay_rows records the skip.

    The ``dict | None`` return type is the new package-level
    convention. Migration 001 never returns ``None``; future
    migrations may.
    """
    if table_name != "security_log":
        return row
    if "severity" in row and row["severity"] in _SEVERITY_MAP:
        row = dict(row)
        row["severity"] = _SEVERITY_MAP[row["severity"]]
    return row
