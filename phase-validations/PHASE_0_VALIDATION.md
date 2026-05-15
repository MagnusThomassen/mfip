# Phase 0 Validation

**Phase:** Environment Setup
**Status:** Complete
**Started:** 2026-05-07
**Completed:** 2026-05-09 (validated retroactively 2026-05-15)
**Validated by:** Magnus Thomassen
**Session:** 16 (retroactive)

---

## Phase deliverables checklist

Derived from `04_BUILD_SEQUENCE.docx` Phase 0 entry.

- [x] Install Claude Desktop app (latest version, Windows)
  - evidence: in-use throughout Sessions 1–16
- [x] Verify Max subscription and Cowork enabled
  - evidence: in-use throughout Sessions 1–16
- [x] Install Claude Code (terminal)
  - evidence: in-use as the build harness from Session 1 onwards
- [x] Install finance plugins from `anthropics/financial-services-plugins`
  - evidence: commit `afcc14d`
- [x] Set up Python 3.12 environment with packages from
  `03_TECH_STACK.docx`
  - evidence: commit `a258675`; `requirements.lock.txt` pinned;
    venv recovery procedure documented in `worklog.md` 2026-05-14
    entry
- [x] Set up Git repository for MFIP project
  - evidence: commit `e556617`
- [x] Create local folder structure under `C:\MFIP\`
  - evidence: 2026-05-09 cleanup pass (`decisions.md` 2026-05-09
    "Pre-Phase-1 cleanup and doc-alignment pass") — eight top-level
    directories confirmed present
- [x] Initialise Git repository in `C:\MFIP\repo\` and create private
  GitHub remote
  - evidence: commit `e556617`
- [x] Bloomberg templates Git-versioned under
  `repo\templates\bloomberg\`
  - evidence: commit `5c9db87` (`decisions.md` 2026-05-09 "Gap 1")
- [x] `.env` created and populated with SMTP credentials
  - evidence: `.env.example` template added in PR #41 (Session 15A);
    real `.env` created manually by Magnus 2026-05-15 between
    Session 15A close and Session 15B kickoff; verified
    `worklog.md` 2026-05-15 close-out entry. Note: this deliverable
    was missing at the original phase-completion checkpoint —
    surfaced in Session 15B; documented in
    `## Issues discovered (fixed in later sessions)` below.

---

## Runtime artifacts verified on disk

Verified during Session 16 retroactive validation (2026-05-15).

- [x] `C:\MFIP\repo\` repository
  - [x] verified existing
  - [x] verified behaving correctly
  - notes: clean working tree at `main` HEAD `1175925`; `git status`
    confirms; `git log --oneline -5` returns expected recent history

- [x] `C:\MFIP\repo\.venv\` (Python 3.12.10)
  - [x] verified existing
  - [x] verified behaving correctly
  - notes: 75 packages installed from `requirements.lock.txt`;
    `python -m pytest -q` returns 56 passed; venv missing
    incident in Session 14 recovered via documented procedure
    (`worklog.md` 2026-05-14)

- [x] `C:\MFIP\repo\.env`
  - [x] verified existing
  - [x] verified behaving correctly
  - notes: UTF-8 without BOM, 17 lines, contains all five
    `MFIP_SMTP_*` keys plus service-account credentials per PR #46;
    gitignored at `.gitignore` line 29; live SMTP exercise via
    `mfip/alerts/sender.py` confirms credentials work (Session 15B
    live alert tests, four success entries in `security_log`)

- [x] `C:\MFIP\bloomberg_archive\<TICKER>\<YYYY-MM-DD>\` structure
  - [x] verified existing
  - [x] verified behaving correctly
  - notes: six ticker folders plus `FX\` and `INDICES\`; each carries
    `2026-05-08\` date subfolder from initial Bloomberg lab session
    (`decisions.md` 2026-05-09 cleanup pass)

- [x] `C:\MFIP\filings\<TICKER>\` structure
  - [x] verified existing
  - [x] verified behaving correctly
  - notes: five ticker folders; durable-artefact pattern (no date
    subfolders) per storage architecture

- [x] `C:\MFIP\docs\` — local working copies of design docs
  - [x] verified existing
  - [x] verified behaving correctly
  - notes: 11 design docs present; `README.md` tracks last sync date
    per `CLAUDE.md` session-start guidance

- [x] GitHub remote — private repo, branch protection on `main`
  - [x] verified existing
  - [x] verified behaving correctly
  - notes: branch protection requires PR + squash-merge; force-push
    blocked; force-push blocking also enforced locally via
    `.claude/hooks/git-guardrails.py` (installed Session 15)

---

## Live exercise log

- 2026-05-15 — `git rev-parse HEAD` → `1175925` (matches expected
  Phase 2 PR-B HEAD)
- 2026-05-15 — `git status` → working tree clean
- 2026-05-15 — `python -m pytest -q` → 56 passed
- 2026-05-15 — `python -m mfip.dashboard` launches without errors
  (smoke check; full Phase 1 exercise lives in
  `PHASE_1_VALIDATION.md`)
- 2026-05-15 — `.env` contents verified via PowerShell length checks
  (Session 15B pre-flight) and live alert test (Session 15B PR #46
  delivery confirmations in `security_log`)

---

## Findings

### Working as intended

- Repo structure, venv, dependency pinning, Bloomberg template
  Git-versioning, GitHub remote, branch protection, and all
  filesystem-level Phase 0 deliverables are in place and behaving
  correctly as of 2026-05-15.

### Issues discovered (fixed in this session)

- None — retroactive validation; no new issues surfaced.

### Issues discovered (fixed in later sessions)

- **`.env` missing despite Phase 0 marked complete.** Discovered
  pre-Session-15B during alert delivery setup. Phase 0 checklist
  listed ".env created" as a deliverable; file did not exist on
  disk. Fixed via PR #41 (`.env.example` template) in Session 15A;
  Magnus created real `.env` manually between Session 15A close
  and Session 15B kickoff. Tracked in `worklog.md` 2026-05-15
  entry (CLOSED).

- **DuckDB schema not initialised on production DB.** Discovered
  during first live alert test in Session 15B. The DB file existed
  (12 KB, auto-created on first DuckDB connect) but contained zero
  application tables. PR-A's `scripts/init_db.py` had never been
  run against the production DB. Fixed in PR #45 (Session 15B) by
  making `init_db.py` idempotent with three-case schema
  verification, running it against the production DB, and adding a
  "First-time setup" section to `README.md`.

### Issues discovered (deferred)

- None.

---

## Lessons feeding into this pattern

Both deferred-fix issues above share one root cause: Phase 0 was
marked complete based on a checklist self-report rather than a
filesystem-state walkthrough. The `.env` deliverable was a line item
that nobody walked through and confirmed existed; the DB schema
deliverable was implicit ("logging substrate works") and similarly
unverified end-to-end. Neither failure was visible until live
exercise forced contact with the artifact.

The `phase-validations/` pattern — established in this same session
in Item 0 — encodes the lesson: every phase close-out requires a
walkthrough document that confirms each deliverable exists on disk
and behaves correctly, signed off by Magnus. Self-reports from
checklists are no longer sufficient to close a phase.

---

## Sign-off

- [x] I have personally walked through every deliverable and runtime
  artifact above and confirmed each one.

**Signed:** Magnus Thomassen
**Date:** 2026-05-15
