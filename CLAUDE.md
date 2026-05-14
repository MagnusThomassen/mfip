# CLAUDE.md — Session Bootstrap for MFIP

You are Claude Code working on MFIP (Magnus Financial Intelligence Platform), a personal finance analysis platform. This file is auto-loaded at session start. Read it before doing anything else.

**Working directory:** `C:\MFIP\repo\`

## Project context

MFIP is a multi-agent financial analysis pipeline that takes company filings and Bloomberg data and produces professional investment recommendations presented in a Plotly Dash desktop app. It is a personal learning project for Magnus, an MSc Finance student at Kingston University London. It is **not** a production trading system, **not** a multi-user tool, and **not** related to his MSc dissertation (which is a separate Claude project). If insights from MFIP work appear structurally transferable beyond MFIP, flag them with a one-line note suggesting Magnus log them in `C:\Dissertation\inbox\transferable_from_mfip.md` — but do not write to that file directly and do not engage with dissertation content.

## Terminology

These terms are canonical across all MFIP discussions, design docs, decisions log, and ideas log. Use them consistently; do not invent synonyms.

| Term | Refers to |
|---|---|
| Project Knowledge | The Claude Project file library / knowledge base — docs uploaded to the chat-based Claude project. Anthropic's own term for it. What chat-based Claude reads. |
| Local repo | `C:\MFIP\` on the Windows machine — the actual working tree where code is built and run. |
| GitHub | `github.com/MagnusThomassen/mfip` — the published remote, including rulesets, PRs, and repo metadata. |
| Design docs | The numbered `.docx` files (`00_PROJECT_OVERVIEW.docx` through `07_BLOOMBERG_EXPORT_TEMPLATE.docx`) plus `SYSTEM_PROMPT.docx`. Live in Project Knowledge; local working copies at `C:\MFIP\docs\`. |
| Repo docs | `CLAUDE.md`, `decisions.md`, `ideas.md`, `worklog.md`, `MEMORY.md`, `README.md` — Markdown files Git-versioned in the local repo. |
| Bloomberg templates | The three `.xlsx` master templates (`Master`, `FX`, `Indices`). Defines the export contract. Git-versioned under `repo\templates\bloomberg\`. |
| Bloomberg export files | The actual saved exports in `bloomberg_archive\<TICKER>\<YYYY-MM-DD>\`. The data, not the contract. |
| Validator | Reserved for `scripts/ingestion/validate_bloomberg_workbook.py` specifically. Future ingestion components (parser, reconciliation engine) get their own names. |
| Phase | A build sequence phase (Phase 0, Phase 1, …) per `04_BUILD_SEQUENCE.docx`. |
| Session | One Claude conversation. |
| Item | A numbered task within a session. |

## How to start each session

1. Read `decisions.md` in the local repo to catch up on architectural decisions made in chat sessions.
2. Check `git log --oneline` to see recent build progress.
3. Design docs: local working copies live at `C:\MFIP\docs\`. Project Knowledge is the canonical source; local copies are working copies that may drift. `C:\MFIP\docs\README.md` tracks the last sync date.
   - **Routine lookups** (colour values, sheet names, zone dimensions) — read local, no confirmation needed.
   - **Architectural reads** (constraints, agent contracts, decisions you'll encode in code) — read local, then ask the user: "`docs\README.md` last sync is `<date>`. Is Project Knowledge newer?"
   - If the user says Project Knowledge is newer, ask them to paste the relevant section. Do not proceed on potentially-stale guidance.

## Division of responsibilities

- **Chat-based Claude (architect):** owns design decisions, agent prompt drafting, doc revisions, architecture reasoning. Updates `decisions.md` content (passed to you for committing).
- **You (Claude Code, builder):** own code implementation, file edits, test execution, Git operations, package management, debugging.

When in doubt about a design question, do not improvise — ask the user to take it to the chat-based Claude first.

## Architectural rules you must respect

These are non-negotiable and come from the design docs:

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

The layout encodes a deliberate asymmetry: Bloomberg export files are point-in-time snapshots (date-versioned subfolders); annual report PDFs are durable artefacts (no date subfolders, identified by fiscal year in filename).

`<TICKER>` below is the Bloomberg-style ticker with exchange suffix (e.g. `EQNR_NO`, `CKN_LN`, `MSFT_US`), used consistently across `bloomberg_archive\`, `filings\`, and `models\`.

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
    ├── ideas.md
    ├── worklog.md
    ├── MEMORY.md
    ├── requirements.txt
    ├── requirements.lock.txt
    ├── .gitignore
    ├── .env                              ← Gmail SMTP creds; gitignored; loaded via python-dotenv
    ├── CLAUDE.md
    ├── README.md
    ├── LICENSE
    ├── scripts\
    │   ├── smoke_test_env.py
    │   ├── ingestion\
    │   │   └── validate_bloomberg_workbook.py
    │   └── (dashboard, watchers, scheduled_tasks, agents added per phase)
    ├── templates\bloomberg\              ← Git-versioned Bloomberg templates
    │   ├── Template_FX\
    │   ├── Template_Index\
    │   └── Template_Ticker\
    └── design\                           ← JSX prototype, visual reference only (not a deliverable)
```

## Coverage universe (v1)

Six companies: EQNR (primary test company), DNB, TEL, NOVO B, MSFT, CKN.

## Current status

**Phase 0 complete.** Repo initialised, GitHub remote configured with branch protection on `main`, Python 3.12 venv with pinned dependencies (`requirements.txt` + `requirements.lock.txt`), finance plugins installed, smoke test passing, Bloomberg templates Git-versioned under `repo\templates\bloomberg\`, validator built and proven against the 2026-05-08 archive.

**Phase 1 next: dashboard shell.** Plotly Dash + AG Grid, four zones, placeholder data throughout. Estimated 3–5 hours. See `04_BUILD_SEQUENCE.docx` Phase 1 and `05_DASHBOARD_SPEC.docx` for the zone specifications.

## Commit message convention

Subject line: imperative mood, under 72 characters, with a prefix from the set below. Body: optional, separated by a blank line, used for non-trivial changes.

| Prefix | When to use |
|---|---|
| `feat` | New code or functionality (validators, agents, scripts, dashboard panels) |
| `fix` | Bug fix |
| `docs` | Documentation: `CLAUDE.md`, `README.md`, references to design docs |
| `decision` | Appending to `decisions.md` |
| `ideas` | Appending to or graduating items from `ideas.md` |
| `worklog` | Appending to or closing items in `worklog.md` |
| `chore` | Repo maintenance and config (`.gitignore`, `requirements.txt` bumps) |
| `backup` | Backup infrastructure changes (restic, Task Scheduler entries) |
| `test` | Test or probe commit (rare; usually thrown away in squash-merge) |

Examples:

- `feat(ingestion): add Bloomberg saved-file workbook validator`
- `docs: align CLAUDE.md storage layout to disk`
- `decision: 2026-05-10 pre-Phase-3 Bloomberg validator`
- `chore: pin pandas to 2.2.3`

Optional scope in parentheses (e.g. `feat(ingestion):`, `docs(claude-md):`) when the prefix alone doesn't disambiguate.

## Working with branch protection

`main` is protected: no direct push, no force push, no merge commits. Every change to `main` goes through a PR with squash-or-rebase merge. Admin bypass is limited to PRs.

Practical implication for routine doc edits (`CLAUDE.md`, `decisions.md`, `ideas.md`, `worklog.md`, `MEMORY.md`, `README.md`):

- **Local-branch flow** (full control, slower): create branch → commit → push → open PR → squash-merge → pull main → delete branch. Use this for substantive edits or anything touching multiple files.
- **GitHub web UI** (faster for small edits): open the file on GitHub, click the pencil icon, edit, commit straight to a new branch with PR. GitHub handles the branch creation and PR opening in one flow. Use this for typo fixes, small clarifications, single-line edits. Pull main locally afterwards.

Either flow respects branch protection. Choose by edit size.

## When updating decisions.md

Decisions are made in chat sessions, not by you. The user will paste new entries. Append them to `decisions.md`, commit with message format: `decision: <short summary>`. Do not invent decisions or rephrase them.

**Commit decisions.md in the same commit as the code it documents, not as a follow-up commit.** A squash-merge captures exactly the commits on the branch at merge time — a trailing decisions.md commit pushed after the merge races the merge and will be left out.

**Index-touch rules (per the 2026-05-14 self-indexing decision):**

Every new `## YYYY-MM-DD` entry requires two additional edits in the same commit:

1. **Tags line.** Add `**Tags:** <tag>` on the line immediately after the heading (no blank line between heading and tag line). Choose one tag from the locked taxonomy: `architecture`, `infrastructure`, `data-contract`, `process`, `docs`. When two tags apply equally, use the one that best matches *retrieval intent* — the question a future reader would ask when looking for this entry.

2. **TOC line.** Prepend a new line at the top of the `## Index` section (newest-first):
   ```
   - [YYYY-MM-DD — <summary>](#<auto-anchor>) `<tag>`
   ```
   Summary rules: ≤80 chars; describes what the entry is about, not what it concludes.
   Anchor algorithm: GitHub lowercases, replaces spaces with hyphens, strips non-word/non-space/non-hyphen chars. Em-dashes (` — `) become `--`. Verify post-push using GitHub's rendered TOC if in doubt.

These two edits are not optional — an entry without a tag or a TOC line is incomplete.

## When updating ideas.md and worklog.md

Two backlog files split by lifetime, per the 2026-05-13 decision in
`decisions.md`:

- **`ideas.md`** — forward-looking, phase-gated items (future features,
  skills/plugins/agents, design questions deferred to later phases).
  Items keep `IDEA-NNN` prefix where applicable. Decision gates measured
  in *phases*.
- **`worklog.md`** — in-flight observations and bug-shaped items that
  close within sessions or days. Date-prefixed entries (no `IDEA-NNN`).
  Statuses: `OPEN` / `CLOSED-<reason>` / `MOVED-TO-IDEAS`. Decision
  gates measured in *days* or "next session".

**Boundary rule:** if its decision gate is measured in *phases*, it's
an idea. If measured in *days* or "next session," it's a worklog item.

As with `decisions.md`, content is drafted in chat sessions and pasted
to you for committing. Commit messages: `ideas: <summary>` and
`worklog: <summary>`.

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
