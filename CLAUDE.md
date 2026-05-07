# CLAUDE.md — Session Bootstrap for MFIP

You are Claude Code working on MFIP (Magnus Financial Intelligence Platform), a personal finance analysis platform. This file is auto-loaded at session start. Read it before doing anything else.

## Project context

MFIP is a multi-agent financial analysis pipeline that takes company filings and Bloomberg data and produces professional investment recommendations presented in a Plotly Dash desktop app. It is a personal learning project for Magnus, an MSc Finance student at Kingston University London. It is **not** a production trading system, **not** a multi-user tool, and **not** related to his MSc dissertation (which is a separate Claude project).

## How to start each session

1. Read `decisions.md` in this repo to catch up on architectural decisions made in chat sessions.
2. If the user references a design doc (e.g. "the architecture spec" or "01_ARCHITECTURE"), the canonical version lives in the chat-based Claude project knowledge base — ask the user to paste the relevant section if you need it. The repo does not contain the design docs.
3. Check `git log --oneline` to see recent build progress.

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
6. **Power Automate handles logistics, Claude agents handle intelligence.** Don't put analytical reasoning in Power Automate flows; don't put file watching or scheduling in agent code.
7. **Bloomberg backtesting and the Learning Agent are v2 backlog.** Do not build them in v1, even if it would be elegant.

## Storage layout

Local Windows filesystem only. No SharePoint, no OneDrive for Business integration.

```
C:\MFIP\
├── bloomberg_inbox\
├── bloomberg_archive\
├── filings\<TICKER>\
├── models\<TICKER>\<DATE>\
├── theses\
├── logs\
│   ├── mfip.duckdb
│   └── exports\
└── repo\           ← you are here
```

## Coverage universe (v1)

Six companies: EQNR (primary), DNB, TEL, NOVO B, MSFT, CKN.

## Current status

Pre-build. Repo initialised, decisions log committed, this bootstrap file added. Next phase: Phase 0 — environment setup. See `04_BUILD_SEQUENCE.docx` (in the chat project knowledge base).

## When updating decisions.md

Decisions are made in chat sessions, not by you. The user will paste new entries. Append them to `decisions.md`, commit with message format: `decision: <short summary>`. Do not invent decisions or rephrase them.
