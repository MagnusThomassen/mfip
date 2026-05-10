# CLAUDE.md — Session Bootstrap for MFIP

You are Claude Code working on MFIP (Magnus Financial Intelligence Platform), a personal finance analysis platform. This file is auto-loaded at session start. Read it before doing anything else.

## Project context

MFIP is a multi-agent financial analysis pipeline that takes company filings and Bloomberg data and produces professional investment recommendations presented in a Plotly Dash desktop app. It is a personal learning project for Magnus, an MSc Finance student at Kingston University London. It is **not** a production trading system, **not** a multi-user tool, and **not** related to his MSc dissertation (which is a separate Claude project).

## How to start each session

1. Read `decisions.md` in this repo to catch up on architectural decisions made in chat sessions.
2. Check `git log --oneline` to see recent build progress.
3. Design docs: local copies live at `C:\MFIP\docs\`. The chat-based Claude project knowledge base is the canonical source; local copies are working copies that may drift. `C:\MFIP\docs\README.md` tracks the last sync date.
   - **Routine lookups** (colour values, sheet names, zone dimensions) — read local, no confirmation needed.
   - **Architectural reads** (constraints, agent contracts, decisions you'll encode in code) — read local, then ask the user: "`docs\README.md` last sync is `<date>`. Is the chat project library newer?"
   - If the user says the chat project is newer, ask them to paste the relevant section. Do not proceed on potentially-stale guidance.

## Division of responsibilities

- **Chat-based Claude (architect):** owns design decisions, agent prompt drafting, doc revisions, architecture reasoning. Updates `decisions.md` content (passed to you for committing).
- **You (Claude Code, builder):** own code implementation, file edits, test execution, Git operations, package management, debugging.

When in doubt about a design question, do not improvise — ask the user to take it to the chat-based Claude first.

## Architectural rules you must respect

These are non-negotiable and come from the project design docs:

1. **Extractor A and Extractor B never share context.** Independence is the accuracy guarantee. If you find yourself importing one into the other, stop.
2. **Security Council reports directly to Magnus, never through the Orchestrator.** Any code that routes security alerts via the Orchestrator is a bug.
3. **Security Log is append-only.** No UPDATE or DELETE operations. Enforce in the Python layer; refuse the operation if attempted.
4. **No agent skips a layer.** Data flows Extraction → Reconciliation → Validation → Intelligence Synthesis → Modelling → Recommendation. No shortcuts.
5. **Pydantic schema validation at every agent handoff.** Schema violations trigger a Security Council Advisory.
6. **Python handles logistics, Claude agents handle intelligence.** The logistics layer is `watchdog` (file events), Windows Task Scheduler (scheduled jobs), and `mfip_alerts.py` over Gmail SMTP (structured alerting). Don't put analytical reasoning in the logistics layer; don't put file watching, scheduling, or email delivery in agent code.
7. **Bloomberg backtesting and the Learning Agent are v2 backlog.** Do not build them in v1, even if it would be elegant.
8. **Bloomberg = market data only.** Financial statements come from annual report PDFs via Extractor A. Bloomberg's normalised FA data is excluded by design.
9. **FSA Agent is a hard prerequisite for RE Valuation Agent.** RE cannot run without reformulated statements.

## Storage layout

Local Windows filesystem only. No SharePoint, no OneDrive for Business as a runtime component. (University OneDrive is used as a one-way courier between the Kingston Bloomberg lab and the home machine — see `07_BLOOMBERG_EXPORT_TEMPLATE.docx` STORAGE LAYOUT.)

The layout encodes a deliberate asymmetry: Bloomberg data is point-in-time snapshots (date-versioned subfolders); annual report PDFs are durable artefacts (no date subfolders, identified by fiscal year in filename).

```
C:\MFIP\
├── bloomberg_inbox\                      ← dormant in v1; future infrastructure
├── bloomberg_archive\
│   ├── <TICKER>\<YYYY-MM-DD>\<TICKER>_<YYYY-MM-DD>.xlsx   ← per-company snapshots
│   ├── INDICES\<YYYY-MM-DD>\INDICES_<YYYY-MM-DD>.xlsx     ← shared workbook
│   └── FX\<YYYY-MM-DD>\FX_<YYYY-MM-DD>.xlsx               ← shared workbook
├── filings\<TICKER>\                     ← annual report PDFs (flat, no date subfolder)
├── models\<TICKER>\<DATE>\               ← agent-generated Excel models (DCF, FSA, Comps, Shock)
├── theses\                               ← Chief Analyst Word documents
├── docs\                                 ← local working copies of design docs (.docx + README.md)
├── logs\
│   ├── mfip.duckdb                       ← decision_log + security_log
│   └── exports\                          ← nightly JSON exports, committed to logs-archive branch
└── repo\                                 ← you are here
    ├── decisions.md
    ├── requirements.txt
    ├── requirements.lock.txt
    ├── .gitignore
    ├── .env                              ← Gmail SMTP creds; gitignored; loaded via python-dotenv
    ├── CLAUDE.md
    ├── scripts\
    │   ├── smoke_test_env.py
    │   ├── ingestion\
    │   │   └── validate_bloomberg_workbook.py
    │   └── (dashboard, watchers, scheduled_tasks, agents added per phase)
    └── templates\bloomberg\              ← Git-versioned Bloomberg export masters
        ├── Template_FX\
        ├── Template_Index\
        └── Template_Ticker\
```

## Coverage universe (v1)

Six companies: EQNR (primary test company), DNB, TEL, NOVO B, MSFT, CKN.

## Current status

**Phase 0 complete.** Repo initialised, GitHub remote configured, Python 3.12 venv with pinned dependencies (`requirements.txt` + `requirements.lock.txt`), finance plugins installed, smoke test passing, Bloomberg master templates Git-versioned under `repo\templates\bloomberg\`.

**Phase 1 next: dashboard shell.** Plotly Dash + AG Grid, four zones, placeholder data throughout. Estimated 3–5 hours. See `04_BUILD_SEQUENCE.docx` Phase 1 and `05_DASHBOARD_SPEC.docx` for the zone specifications.

## When updating decisions.md

Decisions are made in chat sessions, not by you. The user will paste new entries. Append them to `decisions.md`, commit with message format: `decision: <short summary>`. Do not invent decisions or rephrase them.

## Ending a session

Sessions end when the user explicitly says so (e.g. "session over", "we're done for today", "stopping here"). When the user signals end of session, your final reply must be a **handoff prompt for the next session** — written so that you (or another Claude Code session) can pick up exactly where this one stopped without re-reading the full conversation.

The handoff prompt must include:

- **Where we left off** — last completed action, last commit hash if relevant.
- **Current state** — clean working tree, uncommitted work, any tools/processes still running, any open prompts awaiting user input.
- **Next action** — the single next concrete step, specific enough to act on without re-deriving context.
- **Open questions or blockers** — anything the next session needs to resolve before progressing.
- **Files touched this session** — short list, so the next session knows what changed.

Format: a single Markdown block the user can paste into the next session's first message. No closing pleasantries, no "good luck" — it's a working handoff, not a sign-off.

Do not infer end-of-session from the conversation tailing off, the user going quiet, or work appearing complete. Wait for explicit instruction.