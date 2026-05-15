# MFIP — Memory

> **Source of truth for current project state.**
> Updated at the end of every session, before the handoff prompt is written.
> Git-tracked. Every change committed with message `memory: <what changed>`.
> Keep under 300 lines. This is the map, not the territory.

---

## Current Focus

**Phase 2 — Logging Infrastructure** (in progress)

PR-A landed: DuckDB schema (`decision_log` + `security_log`), Pydantic models, log writers with append-only enforcement at the module-API layer, pipeline `contextvars`-based correlation-ID module, round-trip tests including cross-log JOIN coverage. PR-B landed: `mfip/alerts/` — Alert Pydantic model + multipart MIME renderer + SMTP sender with fallback queue under `runtime/unsent_alerts/` and drain-on-every-send. PR-C (Task Scheduler nightly export to `logs-archive` branch) remains.

---

## Phase Status

| Phase | Name | Status | Notes |
|---|---|---|---|
| 0 | Environment Setup | ✅ Complete | Commits `a258675`, `e556617`, `5c9db87`, `af3f02d`, `dac7e3b` |
| 1 | Dashboard Shell | ✅ Complete | Sessions 5–10; final commit `a9cca58` |
| 2 | Logging Infrastructure | 🟡 In progress | PR-A merged: schema, writers, context. PR-B and PR-C remaining |
| 3 | Bloomberg Ingestion | ⬜ Not started | Requires lab visit |
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
| Bloomberg validator | `scripts/ingestion/validate_bloomberg_workbook.py` | PASS / ADVISORY / FAIL; encodes 07_BLOOMBERG_EXPORT_TEMPLATE.docx contract |
| `CLAUDE.md` | `repo\CLAUDE.md` | Session-bootstrap file for Claude Code; rewritten 2026-05-09 |
| `theme.py` | `mfip/dashboard/theme.py` | Both dark + light token sets; `apply_theme(fig, mode)` helper |
| Theme CSS | `assets/theme.css` | `[data-theme]` selectors; defines all color tokens on `:root`/`html`; mirrors theme.py DARK + LIGHT |
| AG Grid overrides | `assets/ag-grid-overrides.css` | CSS vars from same token set as theme.py; sync enforced by unit test |
| `app.py` | `mfip/dashboard/app.py` | Dash Pages app; imports `pages/home` + `pages/analysis`; `dcc.Location` + theme stores; clientside callback for OS theme detection (inline string form) |
| `pages/home.py` | `mfip/dashboard/pages/home.py` | Home stub at `/`; placeholder content + link to `/analysis` |
| `pages/analysis.py` | `mfip/dashboard/pages/analysis.py` | Analysis page at `/analysis`; composes Zone 1 + Zone 2-4 placeholder containers (CSS Grid layout, 60/40 × 65/35 proportions per spec) |
| Analysis layout CSS | `mfip/dashboard/assets/analysis-layout.css` | CSS Grid for Zone 2-4 placeholder layout; replaces nothing (new) |
| `zone1.py` | `mfip/dashboard/zones/zone1.py` | Zone 1 Command Centre; exports `layout` as module-level constant; composed into `pages/analysis.py` (not a page itself) |
| Theme tests | `tests/test_theme.py` | 8 passing |
| App tests | `tests/test_app.py` | 7 passing (includes `/` and `/analysis` route registration tests) |
| Zone 1 tests | `tests/test_zone1.py` | 9 passing; 24 total green on branch `phase1/routing-restructure` |
| `MEMORY.md` | `repo\MEMORY.md` | This file; added Session 7 |
| `phase-validations/` | `repo\phase-validations\` | Per-phase validation pattern — `_template.md` canonical structure; one `PHASE_N_VALIDATION.md` per phase; PHASE_0 retroactive (2026-05-15) |
| `decision_log` + `security_log` DuckDB tables | `C:\MFIP\runtime\mfip.duckdb` | Schema per `decisions.md` 2026-05-14 entries + 2026-05-15 severity Title-case; init via `python scripts/init_db.py`; migrate via `python scripts/init_db.py --migrate` |
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
| Alerts | Gmail SMTP (`magnus.thomass1@gmail.com` → `magnus.t@live.no`); local fallback to `runtime\unsent_alerts\` | 2026-05-07 |
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
| `security_log` schema extension | Nullable `correlation_id` column added for symmetry with `decision_log`; supersedes `06_SECURITY_COUNCIL.docx` schema text | 2026-05-14 |
| Severity casing | Title-case (`Critical`/`Warning`/`Advisory`) across both `Alert` and `SecurityLogEntry` models | 2026-05-15 |
| Served-layout callback smoke test | Open for Phase 2 close-out (IDEA-023 in `ideas.md`) | — |
| AG Grid dark↔light visual check | Open; 5-minute manual at next app launch | — |

---

## Open Loops

| Loop | Where tracked |
|---|---|
| `watchdog` scope decision (option a/b/c) | Phase 3 build-start deliverable; `04_BUILD_SEQUENCE.docx` |
| PDF filename convention | Phase 4 build-start deliverable; log in `decisions.md` when decided |
| Home screen contents | Design TBD; revisit after `/analysis` is in routine use. `ideas.md` 2026-05-10 "Project Dashboard View" RESOLVED-PARTIALLY |
| ANR enhancements (Bloomberg) | Deferred until next lab session |
| Learning Agent / backtesting | V2; `ideas.md` BACKLOG |
| Web-first migration | Revisit trigger: Mac Mini acquisition autumn 2026 |
| Chief Analyst default weighting (35/35/20/10) | Revisit after 30 recommendations in v2 |
| MAX date preset (Zone 1) | `ideas.md` IDEA-021 PROPOSED; wire at Phase 2+ when data loading is real |
| Overlay chrome ownership (settings panel, alert feed, Security Alert Overlay) | Decide at Alert Feed Panel build |
| Served-layout callback smoke test | `ideas.md` IDEA-023 APPROVED; Phase 1 close-out deliverable |
| Zone 1 chrome styling completeness (focus rings, badge styling, theme application) | `worklog.md` — multiple OPEN entries; re-evaluate when Zone 2 ships |
| Phase 1 close-out tidy-up | `worklog.md` — all four items CLOSED (CLAUDE.md repo path, `__main__.py` confirmation, line-endings normalisation, theme visual application) |

---

## Universe

| # | Ticker | Company | Sector | Role |
|---|---|---|---|---|
| 1 | EQNR | Equinor | Energy | Norway — primary test company |
| 2 | DNB | DNB | Financials | Norway |
| 3 | TEL | Telenor | Telecom | Norway |
| 4 | NOVO B | Novo Nordisk | Healthcare | Denmark |
| 5 | MSFT | Microsoft | Technology | USA |
| 6 | CKN | Clarkson | Shipbroking | UK |

All phases use EQNR as the test company until Phase 9 scales to full universe.

---

## Four Portfolio Strategies

| Strategy | Horizon | Focus |
|---|---|---|
| Core Long-Term | 5–10 years | Quality compounders |
| Active Short-Term | 1–6 months | Tactical |
| Conservative Income | — | Capital preservation, dividends |
| Alpha Fund | — | Concentrated; 10% annual return target |

---

## Key Paths

```
C:\MFIP\
├── repo\                  ← Git root
│   ├── mfip\              ← Python package
│   │   └── dashboard\     ← Dash app
│   │       ├── theme.py
│   │       ├── app.py
│   │       ├── __main__.py    ← enables `python -m mfip.dashboard`
│   │       ├── pages\
│   │       │   ├── home.py        ← /
│   │       │   └── analysis.py    ← /analysis (composes Zone 1)
│   │       ├── zones\
│   │       │   └── zone1.py       ← component, not a page
│   │       └── assets\    ← ag-grid-overrides.css
│   ├── scripts\
│   │   ├── ingestion\     ← validate_bloomberg_workbook.py
│   │   └── backup\        ← Task Scheduler XMLs
│   ├── templates\
│   │   └── bloomberg\     ← Master xlsx templates (Git-versioned)
│   ├── tests\
│   │   ├── test_app.py
│   │   ├── test_theme.py
│   │   └── test_zone1.py
│   ├── CLAUDE.md          ← Claude Code session bootstrap
│   ├── decisions.md
│   ├── ideas.md
│   ├── worklog.md
│   └── MEMORY.md          ← this file
├── bloomberg_archive\     ← exported Bloomberg data (off Git)
├── filings\               ← annual report PDFs (off Git)
├── docs\                  ← local copies of design docs
└── runtime\
    └── unsent_alerts\     ← alert fallback (off Git)
```

---

## Document Index

| File | Contents | Canonical location |
|---|---|---|
| `SYSTEM_PROMPT.docx` | Project instructions; behaviour rules | Claude project library |
| `00_PROJECT_OVERVIEW.docx` | Vision, principles, glossary | Claude project library |
| `01_ARCHITECTURE.docx` | Full system architecture | Claude project library |
| `02_AGENT_DESCRIPTIONS.docx` | All 21 agents specified | Claude project library |
| `03_TECH_STACK.docx` | Tools and libraries | Claude project library |
| `04_BUILD_SEQUENCE.docx` | Build plan with phases and checklists | Claude project library |
| `05_DASHBOARD_SPEC.docx` | Dashboard specification v1.3 | Claude project library |
| `06_SECURITY_COUNCIL.docx` | Security Council detailed design | Claude project library |
| `07_BLOOMBERG_EXPORT_TEMPLATE.docx` | Bloomberg export contract | Claude project library |
| `decisions.md` | Architectural decisions log — self-indexed (TOC + per-entry tags) | `repo\decisions.md` |
| `ideas.md` | Forward-looking backlog — phase-gated items | `repo\ideas.md` |
| `worklog.md` | In-flight observations and bug-shaped items — days-gated | `repo\worklog.md` |
| `MEMORY.md` | This file — live current-state index | `repo\MEMORY.md` |
| `CLAUDE.md` | Claude Code session bootstrap | `repo\CLAUDE.md` |

---

## Agent Count

**21 agents in v1** across 7 layers + Security Council + Orchestrator.
Layer 5.5 (Thesis Monitor, Agent 21) is non-integer — permanent and intentional.

---

*Last updated: 2026-05-15 — Session 16 Item C-1: Zone 2-4 placeholder containers shipped (Phase 1 deliverable gap close).*
