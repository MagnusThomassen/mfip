# MFIP — Memory

> **Source of truth for current project state.**
> Updated at the end of every session, before the handoff prompt is written.
> Git-tracked. Every change committed with message `memory: <what changed>`.
> Keep under 300 lines. This is the map, not the territory.

---

## Current Focus

**Phase 1 — Dashboard Shell** (in progress)

Part 1 merged as `a5e92b9`. Part 2 in flight — PR #14 in draft pending Part 3 focus diagnosis. Settings-panel density and `:focus-visible` CSS rule landed in PR #14 (27/27 tests green) but browser verification shows the ring is only visible on the company selector, not on the other ~9 Zone 1 interactive elements. Three candidate causes logged as IDEA-026. Next: Session 8 Part 1 — diagnose and fix.

---

## Phase Status

| Phase | Name | Status | Notes |
|---|---|---|---|
| 0 | Environment Setup | ✅ Complete | Commits `a258675`, `e556617`, `5c9db87`, `af3f02d`, `dac7e3b` |
| 1 | Dashboard Shell | 🔄 In progress | Sessions 5–7 Part 1 merged at `a5e92b9`; Part 2 PR #14 in draft pending focus diagnosis |
| 2 | Logging Infrastructure | ⬜ Not started | Can parallel Phase 1 |
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
| Repo + venv | `C:\MFIP\repo\` | Python 3.12.10, `requirements.lock.txt` pinned |
| Folder structure | `C:\MFIP\` | 8 top-level dirs, bloomberg_archive per-company layout |
| `.env` | `C:\MFIP\repo\.env` | Off Git; Magnus holds keys |
| Bloomberg templates | `repo\templates\bloomberg\` | Git-versioned; FX, Indices, Master xlsx + 4 .py support files |
| Bloomberg validator | `scripts/ingestion/validate_bloomberg_workbook.py` | PASS / ADVISORY / FAIL; encodes 07_BLOOMBERG_EXPORT_TEMPLATE.docx contract |
| `CLAUDE.md` | `repo\CLAUDE.md` | Session-bootstrap file for Claude Code; rewritten 2026-05-09 |
| `theme.py` | `mfip/dashboard/theme.py` | Both dark + light token sets; `apply_theme(fig, mode)` helper |
| AG Grid overrides | `assets/ag-grid-overrides.css` | CSS vars from same token set as theme.py; sync enforced by unit test |
| `app.py` | `mfip/dashboard/app.py` | `dcc.Location` routing scaffolded; clientside callback for OS theme detection (inline string form); `theme-mode-store` declared |
| `zone1.py` | `mfip/dashboard/zones/zone1.py` | Zone 1 Command Centre built; theme toggle re-wire complete; 10 zone1 tests passing; 23 total |
| Theme tests | `tests/test_theme.py` | 8 passing |
| Zone 1 tests | `tests/test_zone1.py` | 10 passing; 23 total green on main |
| `MEMORY.md` | `repo\MEMORY.md` | This file; added Session 7 |

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
| Routing | `dcc.Location` scaffolded from Session 5; Home-vs-Zone-1 destination deferred post Zone 1 | 2026-05-11 |
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
| `watchdog` scope decision (option a/b/c) | Phase 3 build-start deliverable; `04_BUILD_SEQUENCE.docx` |
| PDF filename convention | Phase 4 build-start deliverable; log in `decisions.md` when decided |
| Home-vs-Zone-1 destination | `ideas.md` PARTIALLY GRADUATED; revisit after Zone 1 in use |
| ANR enhancements (Bloomberg) | Deferred until next lab session |
| Learning Agent / backtesting | V2; `ideas.md` BACKLOG |
| Web-first migration | Revisit trigger: Mac Mini acquisition autumn 2026 |
| Chief Analyst default weighting (35/35/20/10) | Revisit after 30 recommendations in v2 |
| MAX date preset (Zone 1) | `ideas.md` IDEA-021 PROPOSED; wire at Phase 2+ when data loading is real |
| Overlay chrome ownership (settings panel, alert feed, Security Alert Overlay) | Decide at Alert Feed Panel build |
| Served-layout callback smoke test | `ideas.md` IDEA-023 PROPOSED; decision gate end of Phase 1 |
| Zone 1 focus ring not visible on most elements | `ideas.md` IDEA-026 PROPOSED; PR #14 draft until resolved; Session 8 Part 1 |

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
│   │       ├── zones\
│   │       │   └── zone1.py
│   │       └── assets\    ← ag-grid-overrides.css
│   ├── scripts\
│   │   ├── ingestion\     ← validate_bloomberg_workbook.py
│   │   └── backup\        ← Task Scheduler XMLs
│   ├── templates\
│   │   └── bloomberg\     ← Master xlsx templates (Git-versioned)
│   ├── tests\
│   │   ├── test_theme.py
│   │   └── test_zone1.py
│   ├── CLAUDE.md          ← Claude Code session bootstrap
│   ├── decisions.md
│   ├── ideas.md
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
| `05_DASHBOARD_SPEC.docx` | Dashboard specification v1.2 | Claude project library |
| `06_SECURITY_COUNCIL.docx` | Security Council detailed design | Claude project library |
| `07_BLOOMBERG_EXPORT_TEMPLATE.docx` | Bloomberg export contract | Claude project library |
| `decisions.md` | Architectural decisions log | `repo\decisions.md` |
| `ideas.md` | Ideas backlog (replaced V2_BACKLOG.docx) | `repo\ideas.md` |
| `MEMORY.md` | This file — live current-state index | `repo\MEMORY.md` |
| `CLAUDE.md` | Claude Code session bootstrap | `repo\CLAUDE.md` |

---

## Agent Count

**21 agents in v1** across 7 layers + Security Council + Orchestrator.
Layer 5.5 (Thesis Monitor, Agent 21) is non-integer — permanent and intentional.

---

*Last updated: 2026-05-12 — Session 7 Part 2 in flight; PR #14 in draft pending Part 3 focus diagnosis.*
