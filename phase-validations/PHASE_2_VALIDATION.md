# Phase 2 Validation

**Phase:** Logging Infrastructure
**Status:** In progress (skeleton seeded; PR-C remaining)
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
- [ ] Set up Windows Task Scheduler nightly job (02:00) for log
  export to `logs-archive` Git branch
  - evidence: [PR-C — Session 17]

---

## Runtime artifacts verified on disk

To be confirmed during the Phase 2 validation walkthrough at end
of Session 17.

- [x] `C:\MFIP\runtime\mfip.duckdb` exists with current schema
  - [x] verified existing
  - [x] verified behaving correctly
  - notes: Schema applied via `python scripts/init_db.py` in
    Session 15B (PR #45); migrated to Title-case severity in
    Session 16 (PR #49); contains 3 `security_log` rows from
    live alert tests, all `Advisory`. Pre-migration dump retained
    at
    `C:\MFIP\runtime\migrations\pre-migration-20260515T152930Z.jsonl`
    (gitignored). `row_seq` IDENTITY column added in Session 17
    PR-C-prereq.

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

- [ ] `C:\MFIP\logs\exports\<YYYY-MM-DD>.json` lands on disk after
  nightly export task runs
  - [ ] verified existing
  - [ ] verified behaving correctly
  - notes: [PR-C runtime artifact — verify during Session 17
    walkthrough]

- [ ] `logs-archive` Git branch contains exported JSON file commits
  after nightly export task runs
  - [ ] verified existing
  - [ ] verified behaving correctly
  - notes: [PR-C runtime artifact — verify during Session 17
    walkthrough]

- [ ] Task Scheduler entry registered for nightly export at 02:00
  - [ ] verified existing
  - [ ] verified behaving correctly
  - notes: [PR-C runtime artifact — verify via Task Scheduler GUI
    or `Get-ScheduledTask` during Session 17 walkthrough]

- [ ] `security_log` self-event row written by nightly export task
  recording success or failure
  - [ ] verified existing
  - [ ] verified behaving correctly
  - notes: [PR-C runtime artifact — verify by querying
    `security_log WHERE issue_description LIKE 'nightly_log_export_%:%'`
    during Session 17 walkthrough; expect at least one
    `nightly_log_export_succeeded` row with `correlation_id IS NULL`
    and `severity = 'Advisory'` after manual task trigger]

- [ ] Export-cursor state file at
  `C:\MFIP\runtime\export_state.json` exists and reflects last
  successful export
  - [ ] verified existing
  - [ ] verified behaving correctly
  - notes: [PR-C runtime artifact — verify file contains current
    `row_seq` cursor per log table after manual task trigger]

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
