"""
Migration 002 — Add row_seq BIGINT NOT NULL DEFAULT nextval(...)
as the first column of decision_log and security_log.

Enables monotonic-cursor-based log export (PR-C / Item 2b). Row
order is preserved via per-table dump ORDER BY at the runner
step; historical rows get row_seq values in insertion-time
order.

Transform is identity for row content. The defensive
``row.pop("row_seq", None)`` is load-bearing: with DuckDB's
``DEFAULT nextval()`` (not GENERATED ALWAYS), a row dict
carrying a non-null row_seq would silently override the
sequence. The pop ensures the sequence assigns fresh values.

ONE-SHOT PROPERTY: this migration makes ``--migrate`` one-shot.
After it has landed, re-running ``--migrate`` will dump rows
that include row_seq in their column list (since the column
now exists); the transform pops the value from the row dict,
but the INSERT column list — built from the dump's column
list — still includes row_seq; the result is NULL into a
NOT NULL column for every row, exit 2 with all rows skipped.
This is loud failure, not silent corruption. The JSONL dump
remains on disk as the recovery point. To re-run intentionally
after migration #2: drop both sequences and tables manually,
then re-run from scratch. See decisions.md 2026-05-15 entry on
this migration for the full rationale.
"""

description = "Add row_seq IDENTITY column to decision_log and security_log"


def transform(row: dict, table_name: str) -> dict | None:
    """Identity transform for content; load-bearing row_seq removal.

    The pre-migration dump runs against the old schema (no
    row_seq column) on first apply, so row_seq will not appear
    in dumped rows then. The pop is load-bearing on subsequent
    re-runs (where it would be present) — it prevents a stale
    row_seq value from overriding the sequence's nextval default.
    """
    row.pop("row_seq", None)
    return row
