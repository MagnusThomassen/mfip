# MFIP — Magnus Financial Intelligence Platform

A multi-agent financial analysis pipeline that takes company filings and Bloomberg market data and produces investment recommendations, presented through a Plotly Dash desktop app.

Personal learning project. Built by [Magnus Thomassen](https://github.com/MagnusThomassen), MSc Finance at Kingston University London. Bridges financial-statement analysis, valuation modelling, and applied AI engineering.

> **Status:** See [`STATE.md`](STATE.md) for current phase, what's built, and what's next. See [`decisions.md`](decisions.md) for the architectural design log.

## What it does

The pipeline runs in seven layers, each with strict schema contracts at the handoff:

1. **Extraction** — Two independent agents pull numbers and narrative from annual report PDFs.
2. **Reconciliation & validation** — Cross-checked, page-cited, schema-enforced.
3. **Intelligence synthesis** — News, macro context, sentiment.
4. **Modelling** — DCF, FSA / DuPont, comparables, shock analysis run in parallel.
5. **Recommendation** — A Chief Analyst agent synthesises BUY / HOLD / SELL with thesis.
6. **Portfolio routing** — Strategy Engine routes recommendations into four portfolio strategies (Core Long-Term, Active Short-Term, Conservative Income, Alpha Fund).
7. **Security Council** — Four agents monitor the system itself (training mode, learning-focused).

A Plotly Dash dashboard surfaces the full state — pipeline status, recommendations, portfolio P&L, news feed, security alerts.

## Working on this project with Claude

MFIP is built with two Claude readers, and they read different things. The chat-based Claude (used for design conversations, decisions, and session planning) reads the project library — the `.docx` files in the Claude project knowledge base. Claude Code (used for code, tests, and Git operations) reads the repository directly, with `CLAUDE.md` auto-loaded as its session-bootstrap file.

Both readers need a shared picture of **where the project is right now**: which phase, what's built, recent decisions, what's in flight. That live state lives in [`STATE.md`](STATE.md) at the repo root. Claude Code reads it on every session start. Chat-based Claude has no automatic channel into the repo, so its copy of `STATE.md` must be pasted into the conversation at the top of every chat thread, in a fenced block:

    ```state
    <paste STATE.md content here>
    ```

If a chat thread opens without a `state` block, chat-based Claude treats itself as not having current state and asks for the paste before answering questions that depend on it. Architecture and design questions still work without it. This is deliberate: stale state from a static system prompt is what caused the workflow to be redesigned in the first place.

`STATE.md` is updated in two places. Chat-based Claude drafts an updated `STATE.md` as the first block of its session-close output; Magnus applies it to the repo and commits before opening the next chat thread (`state: <summary>` commit message). Claude Code updates `STATE.md` inline whenever code-side work changes state — a shipped PR, a phase status change, a new active decision — in the same commit as the work itself, and bumps the `Last updated:` line at the top. When the two views disagree, the repo wins: chat-Claude rebases its mental model from the next paste. This convention, plus the rituals encoded in `SYSTEM_PROMPT.docx` and `CLAUDE.md`, is the whole of the cross-reader workflow.

## Coverage universe (v1)

Six companies, picked for sector and geographic diversity:

| Ticker | Company | Sector |
|---|---|---|
| EQNR | Equinor | Energy (Norway) |
| DNB | DNB Bank | Financials (Norway) |
| TEL | Telenor | Telecom (Norway) |
| NOVO B | Novo Nordisk | Healthcare (Denmark) |
| MSFT | Microsoft | Technology (USA) |
| CKN | Clarkson | Shipbroking (UK) |

## Technical stack

- **Agent runtime** — Claude Code + Cowork
- **Languages** — Python 3.12 (analysis, agents), PowerShell (Windows logistics)
- **Dashboard** — Plotly Dash + AG Grid
- **Data** — Annual report PDFs (primary), Bloomberg Excel exports (market data only), yfinance, NewsAPI + FinBERT
- **Storage** — DuckDB (logs), local filesystem (artefacts), Git (code), restic + Backblaze B2 (off-site backup)
- **Schema** — Pydantic at every agent handoff

See `03_TECH_STACK.docx` in the design-doc set for the full list with rationale.

## Repository layout

```
scripts/
  smoke_test_env.py
  ingestion/
    validate_bloomberg_workbook.py     ← Phase-3 contract validator
  backup/
    Invoke-MfipBackup.ps1, Invoke-MfipPrune.ps1, Task-*.xml
templates/bloomberg/                    ← Git-versioned export masters
CLAUDE.md                               ← Session bootstrap for Claude Code
decisions.md                            ← Architectural decisions log
ideas.md                                ← Backlog and graduated ideas
requirements.txt, requirements.lock.txt
```

Design documents live separately in the Claude project knowledge base. They are intentionally not in Git — `.docx` is binary and doesn't diff well; `decisions.md` plus `CLAUDE.md` together provide the architectural record for anyone reading the code in isolation.

## First-time setup

When cloning the repo to a fresh machine, complete these steps before running any code. They produce the runtime artifacts that the codebase depends on but does not version-control.

1. **Create the virtual environment** and install dependencies:

   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   pip install -r requirements.lock.txt
   ```

2. **Create `.env`** by copying the template and filling in real values:

   ```powershell
   Copy-Item .env.example .env
   # Edit .env in your editor — replace placeholder values.
   ```

   See `.env.example` for the full list of expected keys and their purposes.

3. **Initialise the database schema:**

   ```powershell
   python scripts/init_db.py
   ```

   Creates `C:\MFIP\runtime\mfip.duckdb` (or `$env:MFIP_DB_PATH` if set) with the `decision_log` and `security_log` tables. Idempotent — safe to re-run; will verify the schema matches expectations. Pass `--verbose` for per-column detail when drift is detected.

4. **Verify the test suite passes:**

   ```powershell
   python -m pytest
   ```

   Should return all tests green with zero deprecation warnings.

5. **Launch the dashboard** (optional sanity check):

   ```powershell
   python -m mfip.dashboard
   ```

If any step fails, see `worklog.md` for known setup issues, or check `decisions.md` for relevant architectural context.

## What this project is and isn't

**It is:**
- A personal learning tool for finance analysis and AI engineering
- A craft project demonstrating both financial and technical competence
- A portfolio piece built in the open

**It is not:**
- A production trading system
- A multi-user tool
- Connected to my MSc dissertation (which is a separate project)
- Institutional-grade or compliance-ready

## License

[MIT](LICENSE) — free to use, fork, study. No warranty.

## Contact

[github.com/MagnusThomassen](https://github.com/MagnusThomassen)
