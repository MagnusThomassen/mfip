# MFIP — Domain Language

Canonical terminology for MFIP. Every agent file, variable name, and
log message should use these terms consistently. When in doubt, use
the term in this file, not a synonym.

This file covers pipeline and agent terminology. For session and
build terms (Project Knowledge, repo, GitHub, phases, etc.), see
`CLAUDE.md`'s `## Terminology` section.

---

## Pipeline and agent terms

| Term | Refers to | Avoid |
|---|---|---|
| Extraction Layer | Layer 1 — Extractor A + Extractor B running independently on PDF filings. | Extraction stage, PDF layer |
| Extractor A | The primary PDF extraction agent (numbers + narrative). Never shares context with Extractor B. | Primary extractor |
| Extractor B | The independent verification extraction agent. Never shares context with Extractor A. | Secondary extractor |
| Reconciliation Engine | Agent 04 — diffs Extractor A and B outputs, resolves discrepancies. | Reconciler, diff agent |
| Validator Agent | Agent 05 — final independent consistency check. Issues the Validation Certificate. Distinct from the Bloomberg workbook Validator script (see CLAUDE.md). | Checker, approver, Validator (use full name to disambiguate from Bloomberg Validator) |
| Approved Package | The output of the Validator Agent — verified financial data + Validation Certificate. Ready for Layer 3. | Validated data, clean data |
| Validation Certificate | Issued by the Validator Agent. Status: Approved / Conditional / Refused. | Sign-off, approval |
| Enriched Investment Package | Output of the Context Synthesiser — Approved Package + NewsEvents JSON + MacroContext JSON + Investment Context Score. | Enriched data, context package |
| Investment Context Score | 0–100 score summarising the qualitative environment around the data. Produced by Context Synthesiser. | Context score, quality score |
| NewsEvents JSON | Output of the News Agent — chronological feed of material events with category, headline, source, sentiment. | News feed, news data |
| MacroContext JSON | Output of the Macro Agent — directional macro impacts per company. | Macro data, macro feed |
| Reformulated statements | FSA Agent output — financial statements reformulated per Penman methodology (Reformulated_IS, Reformulated_BS). Hard prerequisite for RE Valuation Agent. | Restated statements, adjusted statements |
| Handoff schema | The Pydantic model that validates data passing between two agents. A schema violation triggers a Security Council Advisory. | Data contract, interface spec |
| Security Log | Append-only DuckDB table. No UPDATE or DELETE ever. Read only by Security Council. `correlation_id` nullable for system-level events. | Audit log, event log |
| Decision Log | DuckDB table recording pipeline decisions and events. Written by agents; exported nightly. `correlation_id` required. | Activity log, pipeline log |
| Heartbeat file | `C:\MFIP\runtime\orchestrator.heartbeat` — touched every 60s by the Orchestrator while active. | Status file, ping file |
| Training mode | Security Council v1 operating mode — logs everything but does not auto-suspend the pipeline. | Soft mode, passive mode |
| Coverage universe | The six companies MFIP analyses: EQNR, DNB, TEL, NOVO B, MSFT, CKN. | Portfolio, watchlist |

---

## Flagged ambiguities

- **"Bloomberg data"** was previously used loosely for both export files
  and templates. Resolved: templates = `Bloomberg templates`; data =
  `Bloomberg export files`. (Both rows live in `CLAUDE.md`.)
- **"Validator"** refers to two distinct things: the Bloomberg workbook
  validator *script* (`scripts/ingestion/validate_bloomberg_workbook.py`,
  defined in `CLAUDE.md`) and the *Validator Agent* (Agent 05, defined
  above). Use the full name (`Bloomberg Validator` or `Validator Agent`)
  to disambiguate. Plain "Validator" is reserved for contexts where the
  scope is unambiguous from surrounding text.
