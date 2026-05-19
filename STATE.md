# MFIP — Live State

> **Volatile project state.** Pasted into chat-Claude at session open inside a fenced ```state``` block.
> Updated by Claude Code in the same commit as any state-affecting code change (new PR row in `What Is Built`, phase status flip, new `Active Decisions` row, opened/closed loop). Also redrafted by chat-Claude as block 1 of every session-close output, then applied to the repo by Magnus before opening the next chat thread.
> Git-tracked. Commit message: `state: <what changed>`.
> Keep under 200 lines. This file is the live snapshot, not the archive.
> When editing inline, **always bump the `Last updated:` line below** — staleness checks downstream rely on it.

**Last updated:** 2026-05-19 — Session 19 PR #65: HP_Monthly + HP_Daily array-spill extraction shipped.

---

## Current Focus

**Phase 3 — Bloomberg Ingestion** (in progress; scaffolding complete, sheet extraction next)

PR #62a (validator relocation) and PR #62b (parser scaffolding + handoff schema) shipped 2026-05-19. Per-sheet extraction follows in PRs #63 (BETA + EE scalars), #64 (DVD + HP_Monthly + HP_Daily), #65 (ANR + RV_Comps + `currency.py`), #66 (Indices + FX). Lab visit still pending for the end-to-end exercise (PR #68).

---

## Phase Status

| Phase | Name | Status | Notes |
|---|---|---|---|
| 0 | Environment Setup | ✅ Complete | Commits `a258675`, `e556617`, `5c9db87`, `af3f02d`, `dac7e3b` |
| 1 | Dashboard Shell | ✅ Complete | Sessions 5–10; final commit `a9cca58` |
| 2 | Logging Infrastructure | ✅ Complete | Six PRs across Sessions 14-17; full pipeline with row_seq cursor, nightly export to logs-archive, `phase-validations/PHASE_2_VALIDATION.md` signed off 2026-05-15 |
| 3 | Bloomberg Ingestion | 🟡 In progress | Skeleton seeded 2026-05-18 (Session 18); lab visit pending; watchdog scope is first deliverable |
| 4 | PDF Extraction | ⬜ Not started | |
| 5 | Intelligence Layer | ⬜ Not started | |
| 5.5 | Thesis Monitor Agent | ⬜ Not started | Agent 21; own Task Scheduler XML |
| 6 | Modelling Layer | ⬜ Not started | ~10–14 h estimate |
| 7 | Chief Analyst + Portfolio | ⬜ Not started | |
| 8 | Security Council | ⬜ Not started | Training mode in v1 |
| 9 | Orchestrator + Integration | ⬜ Not started | |

---

## What Is Built

| Item | Location | Notes |
|---|---|---|
| Repo + venv | `C:\MFIP\repo\` | Python 3.12.10, `requirements.lock.txt` pinned. Venv not Git-tracked; recreate via `py -3.12 -m venv .venv` + `pip install -r requirements.lock.txt` if missing. See `worklog.md` 2026-05-14 entry. |
| Folder structure | `C:\MFIP\` | 8 top-level dirs, bloomberg_archive per-company layout |
| `.env` | `C:\MFIP\repo\.env` | Off Git; Magnus holds keys |
| `.env.example` | `repo\.env.example` | Environment variable template; real `.env` is Magnus-side, gitignored, not in repo |
| Bloomberg templates | `repo\templates\bloomberg\` | Git-versioned; FX, Indices, Master xlsx + 4 .py support files |
| Bloomberg validator | `mfip/ingestion/bloomberg/validator.py` (+ thin CLI shell at `scripts/ingestion/validate_bloomberg_workbook.py`) | PASS / ADVISORY / FAIL; encodes 07_BLOOMBERG_EXPORT_TEMPLATE.docx contract; archive-walking helpers extracted into sibling `archive_lookup.py` |
| Bloomberg parser (CONFIG + BETA + EE + HP_Monthly + HP_Daily) | `mfip/ingestion/bloomberg/parser.py` | `parse_workbook(path, *, validation_policy=STRICT) -> ParsedCompanyData`. CONFIG live (with filename-first `ticker_short` derivation via validator's `FILENAME_RE`); BETA + EE scalar extraction live (PR #64) via centralised `_read_scalar` helper + `_NA_VALUES` taxonomy with `#`-prefix guard for unknown Excel/Bloomberg error strings; HP_Monthly + HP_Daily array-spill extraction live (PR #65) via `_read_price_series` helper returning `pandas.Series` with `DatetimeIndex`, terminator at first all-None row (not `max_row`), symmetric `#`-prefix guard on date and value columns. DVD / ANR / RV_Comps still stubbed pending PR #66. `parse_indices_workbook` and `parse_fx_workbook` skeletons. |
| Parser handoff schema | `mfip/ingestion/bloomberg/models.py` | `ParsedCompanyData` Pydantic v2 model + 7 sub-models (Beta, Dividend, EarningsEstimates, AnalystRecommendations, PriceHistory ×2, RVComps); `ParsedIndicesData`, `ParsedFXData`. `arbitrary_types_allowed=True` for `pandas.Series` fields. `config_currency: str` (not `Literal`) so parser doesn't promote validator ADVISORY on non-USD to FAIL. |
| Parser exception hierarchy | `mfip/ingestion/bloomberg/exceptions.py` | `BloombergParserError` (base); `WorkbookValidationError` (validator FAIL + STRICT — carries the full `ValidationReport`); `WorkbookExtractionError` (post-validation extraction problems) |
| `CLAUDE.md` | `repo\CLAUDE.md` | Session-bootstrap file for Claude Code; rewritten 2026-05-09 |
| `theme.py` | `mfip/dashboard/theme.py` | Both dark + light token sets; `apply_theme(fig, mode)` helper |
| Theme CSS | `assets/theme.css` | `[data-theme]` selectors; defines all color tokens on `:root`/`html`; mirrors theme.py DARK + LIGHT |
| AG Grid overrides | `assets/ag-grid-overrides.css` | CSS vars from same token set as theme.py; sync enforced by unit test |
| `app.py` | `mfip/dashboard/app.py` | Dash Pages app; imports `pages/home` + `pages/analysis`; `dcc.Location` + theme stores; clientside callback for OS theme detection (inline string form) |
| `pages/home.py` | `mfip/dashboard/pages/home.py` | Home stub at `/`; placeholder content + link to `/analysis` |
| `pages/analysis.py` | `mfip/dashboard/pages/analysis.py` | Analysis page at `/analysis`; composes Zone 1 + three visible Zone 2-4 placeholder cards (CSS Grid layout 60/40 × 65/35 per spec, with `--border-subtle` chrome and title + "Phase 1 placeholder" caption per card) |
| Analysis layout CSS | `mfip/dashboard/assets/analysis-layout.css` | CSS Grid for Zone 2-4 placeholder layout; replaces nothing (new) |
| `zone1.py` | `mfip/dashboard/zones/zone1.py` | Zone 1 Command Centre; exports `layout` as module-level constant; composed into `pages/analysis.py` (not a page itself) |
| Theme tests | `tests/test_theme.py` | 8 passing |
| App tests | `tests/test_app.py` | 7 passing (includes `/` and `/analysis` route registration tests) |
| Zone 1 tests | `tests/test_zone1.py` | 9 passing; 24 total green on branch `phase1/routing-restructure` |
| `STATE.md` | `repo\STATE.md` | This file; live state snapshot. Split out of the former `MEMORY.md` during the chat-Claude/Claude-Code reader-alignment redesign. |
| `phase-validations/` | `repo\phase-validations\` | Per-phase validation pattern — `_template.md` canonical structure; one `PHASE_N_VALIDATION.md` per phase; PHASE_0 retroactive (2026-05-15) |
| `PHASE_1_VALIDATION.md` | `repo\phase-validations\PHASE_1_VALIDATION.md` | Phase 1 walkthrough validation, signed-off 2026-05-15 (Session 16 Item C); first instance of `phase-validations/_template.md` pattern in active use after the retroactive PHASE_0 |
| `PHASE_2_VALIDATION.md` | `repo\phase-validations\PHASE_2_VALIDATION.md` | Phase 2 walkthrough validation, signed off 2026-05-15 (Session 17 Item 3c); deliverables checklist complete; live exercise covered DB state, alert delivery, nightly export pipeline, and cross-cutting conventions; three findings deferred to `worklog.md` (none blocking Phase 3). Backfilled into `What Is Built` at Session 18 kickoff. |
| `PHASE_3_VALIDATION.md` | `repo\phase-validations\PHASE_3_VALIDATION.md` | Phase 3 skeleton seeded at Session 18 kickoff (2026-05-18); deliverables checklist derived from `04_BUILD_SEQUENCE.docx` Phase 3 entry; awaiting backfill of `evidence:` lines as Phase 3 PRs ship; walkthrough + sign-off pending at close-out. Status: In progress. |
| `decision_log` + `security_log` DuckDB tables | `C:\MFIP\runtime\mfip.duckdb` | Schema per `decisions.md` 2026-05-14 entries + 2026-05-15 severity Title-case; init via `python scripts/init_db.py`; migrate via `python scripts/init_db.py --migrate`; `row_seq` IDENTITY-style column (sequence + DEFAULT nextval) added in Session 17 PR for migration #2 |
| Migrations package | `mfip/logging/migrations/` | One file per migration, numbered prefix; discovered by `scripts/init_db.py --migrate` in numeric order; refactor trigger fired at migration #2 per `decisions.md` 2026-05-15; `002_add_row_seq` adds `row_seq` IDENTITY-style column |
| Nightly log export script | `scripts/scheduled_tasks/nightly_log_export.py` | Exports new `decision_log`/`security_log` rows to JSON in `logs-archive` worktree, commits, pushes; cursor advances on JSON write success; writes self-event rows for all four outcomes |
| Task Scheduler XML — nightly export | `scripts/scheduled_tasks/Task-NightlyLogExport.xml` | Daily 02:00 local; restart-on-failure 3× at 1-min intervals; runs `.venv\Scripts\python.exe` |
| Cursor state file | `C:\MFIP\runtime\export_state.json` | Off Git; per-table last-exported `row_seq`; atomic write via temp + os.replace; managed by `nightly_log_export.py` |
| `logs-archive` worktree | `C:\MFIP\repo-logs-archive\` | Operator one-time setup: `git worktree add C:\MFIP\repo-logs-archive logs-archive`; the export script's working tree |
| Scheduled-task registration script | `scripts/scheduled_tasks/register_tasks.ps1` | Idempotent registration of all four MFIP scheduled tasks (3 backup at `scripts/backup/`, 1 export at `scripts/scheduled_tasks/`) |
| Pydantic log entry models | `mfip/logging/models.py` | `DecisionLogEntry`, `SecurityLogEntry`, `PlaceholderPayload` + `DecisionPayload` discriminated-union scaffold |
| Log writer functions | `mfip/logging/writers.py` | `write_decision`, `append_security_log`; append-only enforced by absence of update/delete functions in module API |
| Pipeline context module | `mfip/pipeline/context.py` | `contextvars.ContextVar` for `correlation_id`; `new_/get_/set_/reset_` API |
| Logging tests | `tests/logging/test_writers.py`, `tests/pipeline/test_context.py` | 12 passing (7 writer + 5 context); 37 total green |
| `mfip/alerts/` | `mfip\alerts\` | Alert model + multipart MIME renderer + SMTP sender with fallback queue and drain-on-send (Phase 2 PR-B) |
| Alerts tests | `tests/alerts/test_models.py`, `tests/alerts/test_renderer.py`, `tests/alerts/test_sender.py` | 18 collected (4 model + 9 renderer with severity parametrize + 5 sender); 55 total green |
| `CONTEXT.md` | `repo\CONTEXT.md` | Canonical pipeline/agent domain language; session/build terms remain in `CLAUDE.md` |
| Debugging protocol | `CLAUDE.md § Debugging protocol` | Six-step loop for runtime-only failures (reproduce → minimise → hypothesise → instrument → fix → regression-test) |
| Git guardrails hook | `.claude/hooks/git-guardrails.py` | Blocks `git push --force` (any variant), `git reset --hard`, destructive `git clean` flags; wired via `.claude/settings.json` `PreToolUse` |

---

## Active Decisions (quick-reference)

| Topic | Decision | decisions.md entry |
|---|---|---|
| Storage | Local filesystem + Git; no SharePoint | 2026-05-07 |
| Python version | 3.12.10 venv; system 3.13.5 untouched | 2026-05-07 |
| Bloomberg | Pull-and-cache at Kingston lab; no live queries | 2026-05-07 |
| Logistics layer | Python (`watchdog` + Task Scheduler + `mfip_alerts.py`); Power Automate removed | 2026-05-07 |
| Alerts | Gmail SMTP service-account separation: `magiconus@gmail.com` → `magnus.thomass1@gmail.com`; local fallback to `runtime\unsent_alerts\` | 2026-05-15 |
| Test invocation | Always `python -m pytest`; never venv shim (ASR blocked) | 2026-05-11 |
| Clientside callbacks | Inline string form ≤30 lines; `assets/clientside.js` only when larger | 2026-05-11 |
| Visual identity | Koyfin-anchored; dual dark+light from start; semantic color tokens; narrowed mono rule | 2026-05-11 |
| Routing | Pages routing; Home (`/`) + analysis (`/analysis`) split; zones are components on `/analysis` | 2026-05-13 |
| Frontend stack | Plotly Dash for v1; web-first (Next.js) revisit after Mac Mini acquisition (autumn 2026) | 2026-05-11 |
| Dashboard folder | `mfip/dashboard/`; scripts/ for operational one-offs only | 2026-05-11 |
| Cross-project firewall | MFIP-Claude flags general patterns only; dissertation synthesis stays in Dissertation project | 2026-05-11 |
| Security Council mode | Training mode in v1 — logs everything, does not auto-suspend pipeline | System prompt |
| Theme toggle cross-layout | Option 3: zone1-local intermediate store `zone1-theme-radio-store` (memory); two-callback relay | 2026-05-12 |
| Overlay chrome ownership | Deferred to Alert Feed Panel build — decide for all three overlays at once | 2026-05-12 |

---

## Open Loops

| Loop | Where tracked |
|---|---|
| Phase 3 lab visit | Required for parser-validator end-to-end exercise and first production `decision_log` row; pre-lab parser scaffolding can land without it against the Git-versioned templates at `templates/bloomberg/`; see `04_BUILD_SEQUENCE.docx` Phase 3 entry |
| PDF filename convention | Phase 4 build-start deliverable; log in `decisions.md` when decided |
| Home screen contents | Design TBD; revisit after `/analysis` is in routine use. `ideas.md` 2026-05-10 "Project Dashboard View" RESOLVED-PARTIALLY |
| ANR enhancements (Bloomberg) | Deferred until next lab session |
| Learning Agent / backtesting | V2; `ideas.md` BACKLOG |
| Web-first migration | Revisit trigger: Mac Mini acquisition autumn 2026 |
| Chief Analyst default weighting (35/35/20/10) | Revisit after 30 recommendations in v2 |
| MAX date preset (Zone 1) | `ideas.md` IDEA-021 PROPOSED; wire at Phase 2+ when data loading is real |
| Overlay chrome ownership (settings panel, alert feed, Security Alert Overlay) | Decide at Alert Feed Panel build |
| Zone 1 chrome styling completeness (popover dismissal, tooltips on display-only indicators) | `worklog.md` — outside-click dismissal cluster + Zone 1 chrome tooltips cluster (Session 16 walkthrough); schedule with Zone 2 build |
| Dash core component overrides (Dropdown, DatePickerRange) | `worklog.md` — architectural entry (Session 16 walkthrough); schedule before Zone 2 first component |
| AG Grid dark↔light visual check | Exercise at Zone 4 first-component build; AG Grid renders only when Zone 4's Holdings Table ships |
