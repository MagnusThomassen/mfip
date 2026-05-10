# MFIP — Magnus Financial Intelligence Platform

A multi-agent financial analysis pipeline that takes company filings and Bloomberg market data and produces investment recommendations, presented through a Plotly Dash desktop app.

Personal learning project. Built by [Magnus Thomassen](https://github.com/MagnusThomassen), MSc Finance at Kingston University London. Bridges financial-statement analysis, valuation modelling, and applied AI engineering.

> **Status:** Phase 0 complete (environment, Bloomberg templates, validator, infrastructure). Phase 1 (dashboard shell) is next. See [`decisions.md`](decisions.md) for the full design log.

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
