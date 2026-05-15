# Phase 2 Validation

**Phase:** Logging Infrastructure
**Status:** PR-C shipped; pending manual walkthrough sign-off (Item 3b)
**Started:** 2026-05-14 (Session 14 — PR-A kickoff)
**Completed:** [YYYY-MM-DD — fill in when PR-C ships and walkthrough completes]
**Validated by:** Magnus Thomassen
**Session:** 17

---

## Phase deliverables checklist

Derived from `04_BUILD_SEQUENCE.docx` Phase 2 entry.

- [x] Design DuckDB schema: `decision_log`, `security_log`
  - evidence: `decisions.md` 2026-05-14 entries "decision_log
    schema: medium structure" and "security_log schema extension"
    (correlation_id nullable column added); schema lives in
    `mfip/logging/schema.sql`; severity normalised to Title-case
    per `decisions.md` 2026-05-15
- [x] Create database initialisation script
  - evidence: `scripts/init_db.py` shipped in PR #36 (Session 14
    PR-A); made idempotent with three-case verification in PR #45
    (Session 15B); gained `--migrate` flag with row-transform
    pattern in PR #49 (Session 16 Item B)
- [x] Create log writer functions
  - evidence: `mfip/logging/writers.py` — `write_decision`,
    `append_security_log`; append-only enforced by absence of
    update/delete functions in module API (PR #36)
- [x] Create schema validation (Pydantic models)
  - evidence: `mfip/logging/models.py` — `DecisionLogEntry`,
    `SecurityLogEntry`, `PlaceholderPayload` + `DecisionPayload`
    discriminated-union scaffold (PR #36); severity Title-case
    Literal per PR #49
- [x] Set up Security Log as append-only
  - evidence: module-API enforcement (no update/delete functions
    in `writers.py`); convention documented in `decisions.md`
    2026-05-14 entry
- [x] Test write/read cycle for both log types
  - evidence: `tests/logging/test_writers.py` (7 tests) +
    `tests/pipeline/test_context.py` (5 tests); cross-log JOIN
    coverage included
- [x] Build `mfip_alerts.py` module
  - evidence: `mfip/alerts/` package shipped in PR #43 (PR-B);
    correlation_id handling refined in PR #44; service-account
    separation in PR #46; severity Title-case pass-through in
    PR #49
- [x] Set up Windows Task Scheduler nightly job (02:00) for log
  export to `logs-archive` Git branch
  - evidence: PR #56 (Session 17 Item 2b) — `scripts/scheduled_tasks/nightly_log_export.py`,
    `scripts/scheduled_tasks/Task-NightlyLogExport.xml`,
    `scripts/scheduled_tasks/register_tasks.ps1` (registers all
    four current tasks). Live exercise produced JSON file
    `C:\MFIP\repo-logs-archive\exports\2026-05-15.json`,
    commit `a6ae66b` on `logs-archive`, self-event row at
    `row_seq=4` in `security_log`. Phase 2 also picked up
    migration #2 (`row_seq` IDENTITY column via PR #55) and the
    migrations-module refactor (PR #54) as prerequisites for
    PR-C's cursor mechanism.

---

## Runtime artifacts verified on disk

To be confirmed during the Phase 2 validation walkthrough at end
of Session 17.

- [x] `C:\MFIP\runtime\mfip.duckdb` exists with current schema
  - [x] verified existing
  - [x] verified behaving correctly
  - notes: Schema applied via `python scripts/init_db.py` in
    Session 15B (PR #45); migrated to Title-case severity in
    Session 16 (PR #49); migrations module refactored to
    `mfip/logging/migrations/` in Session 17 (PR #54);
    `row_seq BIGINT NOT NULL DEFAULT nextval(...)` column added
    as first column of both tables in Session 17 (PR #55, the
    v1.5.2 substitute for IDENTITY per `decisions.md` 2026-05-15).
    Production DB now contains 4 `security_log` rows: 3 Advisory
    from Session 15B live alert tests (`row_seq` 1-3) plus 1
    Advisory `nightly_log_export_succeeded` self-event from
    Item 2b's live exercise (`row_seq=4`). `decision_log` is
    still empty. Pre-migration dumps retained at
    `C:\MFIP\runtime\migrations\` (gitignored): one from PR #49
    severity migration, one from PR #55 row_seq migration. Verify
    during walkthrough:
    `SELECT row_seq, severity, issue_description FROM security_log ORDER BY row_seq`
    returns 4 rows with `row_seq` 1, 2, 3, 4.

- [x] `mfip/logging/` module importable; writers callable
  - [x] verified existing
  - [x] verified behaving correctly
  - notes: 56/56 tests pass on `main` HEAD `7f8e85f`. Round-trip
    tested via `tests/logging/test_writers.py`.

- [x] `mfip/alerts/` module importable; SMTP sender callable
  - [x] verified existing
  - [x] verified behaving correctly
  - notes: Live alert tests in Session 15B confirmed end-to-end
    SMTP path against service account `magiconus@gmail.com` →
    `magnus.thomass1@gmail.com`. Three success rows in
    `security_log` documenting delivery. Re-confirm during Session
    17 walkthrough with one test alert.

- [x] `.env` populated with service-account SMTP credentials
  - [x] verified existing
  - [x] verified behaving correctly
  - notes: Populated 2026-05-15 (post Session 15A PR #41); 17
    lines, UTF-8 without BOM, gitignored at `.gitignore` line 29.

- [x] `runtime/unsent_alerts/` directory created and writable
  - [x] verified existing
  - [x] verified behaving correctly
  - notes: SMTP fallback path; exercised by
    `mfip/alerts/sender.py` drain-on-send logic.

- [ ] JSON export file lands on disk after nightly export task runs
  - [ ] verified existing
  - [ ] verified behaving correctly
  - notes: Path changed from spec — actual location is
    `C:\MFIP\repo-logs-archive\exports\<YYYY-MM-DD>.json`
    (inside the worktree, not under `C:\MFIP\logs\exports\`).
    Item 2b's live exercise produced
    `C:\MFIP\repo-logs-archive\exports\2026-05-15.json`
    (2339 bytes) containing 3 `security_log` rows + export
    metadata. Verify during walkthrough: file exists, opens as
    valid JSON, contains expected `export_metadata` block
    (`exported_at_utc`, `cursor_before`, `cursor_after`,
    `row_counts`), `security_log` array has 3 entries with
    `row_seq` 1-3 in ascending order, `decision_log` array is
    empty.

- [ ] `logs-archive` Git branch contains exported JSON file commits
  after nightly export task runs
  - [ ] verified existing
  - [ ] verified behaving correctly
  - notes: Item 2b's live exercise produced commit `a6ae66b` on
    `logs-archive` with message "nightly log export 2026-05-15 /
    decision_log: 0 rows / security_log: 3 rows (row_seq 1
    through 3) / files_committed: 1". Pushed to
    `origin/logs-archive`. Verify during walkthrough:
    `cd C:\MFIP\repo-logs-archive` then `git log --oneline -3`
    shows the export commit at HEAD; `git log origin/logs-archive --oneline -3`
    shows the same commit pushed remotely.

- [ ] Task Scheduler entry registered for nightly export at 02:00
  - [ ] verified existing
  - [ ] verified behaving correctly
  - notes: Item 2b registered `MFIP-NightlyLogExport` via
    `scripts/scheduled_tasks/register_tasks.ps1`. State=Ready,
    next trigger 2026-05-16T02:00:00 local. Verify during
    walkthrough: `Get-ScheduledTask -TaskName MFIP-NightlyLogExport`
    returns the task with State=Ready and a 02:00 trigger; all
    four tasks (`MFIP-Backup`, `MFIP-Prune`, `MFIP-PruneReminder`,
    `MFIP-NightlyLogExport`) registered idempotently.

- [ ] `security_log` self-event row written by nightly export task
  recording success or failure
  - [ ] verified existing
  - [ ] verified behaving correctly
  - notes: Item 2b's live exercise wrote one
    `nightly_log_export_succeeded` row at `row_seq=4`, severity
    `Advisory`, `correlation_id IS NULL`. Verify during
    walkthrough:
    `SELECT row_seq, severity, issue_description, correlation_id FROM security_log WHERE issue_description LIKE 'nightly_log_export_%:%' ORDER BY row_seq`
    returns at least the one row from Item 2b. Note: this self-
    event row gets captured in the NEXT export run (it lands at
    `row_seq=4`, which is the new cursor's starting predicate),
    so tomorrow's 02:00 run will include it and write its own
    self-event row at `row_seq=5+`. Audit trail compounds
    correctly.

- [ ] Export-cursor state file at
  `C:\MFIP\runtime\export_state.json` exists and reflects last
  successful export
  - [ ] verified existing
  - [ ] verified behaving correctly
  - notes: Item 2b's live exercise populated the file with
    `decision_log: 0`, `security_log: 3`, plus
    `last_export_started_utc` and `last_export_completed_utc`
    timestamps. Verify during walkthrough:
    `Get-Content C:\MFIP\runtime\export_state.json` returns the
    JSON with these four keys, cursor values are integers, and
    `security_log` cursor matches the highest `row_seq` from the
    last export's payload. Cursor advances on JSON write
    success (not commit success) per the Q3 design decision in
    `decisions.md` 2026-05-15.

- [ ] `logs-archive` worktree exists at
  `C:\MFIP\repo-logs-archive\` and is checked out to the
  `logs-archive` branch
  - [ ] verified existing
  - [ ] verified behaving correctly
  - notes: One-time operator setup per Item 2b's `decisions.md`
    2026-05-15 entry "PR-C nightly log export contract".
    Worktree shares the main repo's `.git` directory; the export
    script writes JSON files into the worktree's `exports/`
    subdirectory and commits from there, leaving the main
    checkout's branch state untouched. Verify during walkthrough:
    `cd C:\MFIP\repo` then `git worktree list` shows two entries
    — main checkout on `main` and worktree on `logs-archive`;
    the worktree at `C:\MFIP\repo-logs-archive\` contains an
    `exports/` directory with the JSON file from Item 2b's live
    exercise.

---

## Live exercise log

[Populate during Session 17 walkthrough after PR-C merges.]

---

## Findings

[Populate during Session 17 walkthrough.]

### Working as intended

[List confirmed during walkthrough.]

### Issues discovered (fixed in this session)

[Any in-session fixes — likely tied to PR-C.]

### Issues discovered (fixed in later sessions)

[Likely empty unless something surfaces that fits this bucket.]

### Issues discovered (deferred)

[Any items logged to worklog or ideas.]

---

## Sign-off

- [ ] I have personally walked through every deliverable and
  runtime artifact above and confirmed each one. New findings
  (if any) are logged in `worklog.md` or `ideas.md` per the
  boundary rule.

**Signed:** Magnus Thomassen
**Date:** [YYYY-MM-DD]
