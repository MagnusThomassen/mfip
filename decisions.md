# MFIP — Architectural Decisions Log

This file records non-trivial architectural decisions made during the design and build of MFIP. Both the chat-based Claude (architect) and Claude Code (builder) reference this file to stay aligned. Add a new entry whenever a decision is made that affects more than one component or contradicts/refines the original design docs.

Format: date, decision, reasoning, implication, affected docs.

---

## 2026-05-07 — Storage layer: local filesystem + Git, not SharePoint

**Decision:** MFIP will use local Windows filesystem (`C:\MFIP\`) as the primary file store, with Git/GitHub for code and prompt versioning. No SharePoint or OneDrive for Business integration.

**Reasoning:** Magnus does not have access to a personal SharePoint and cannot connect workplace or university SharePoint to the project. Personal Microsoft 365 was considered (~£60/year) but rejected as unnecessary cost for v1. Local + Git is sufficient for a single-user system, gives full control, and Power Automate Desktop handles local folder watching natively.

**Implication:**
- Power Automate uses Desktop flows for file watching (Bloomberg inbox, log archive triggers).
- Cloud flows still used for Teams notifications, Outlook digest, RSS aggregation.
- DuckDB live file stays local; nightly JSON exports committed to Git for point-in-time recovery.
- Excel models versioned via date-stamped folders, optionally Git-LFS later if history matters.
- External backup (e.g. weekly copy to external drive or personal OneDrive) recommended but not part of MFIP runtime architecture.

**Affected docs:** `01_ARCHITECTURE.docx`, `03_TECH_STACK.docx`, `04_BUILD_SEQUENCE.docx` — all updated 2026-05-07.

**Revisit trigger:** If Magnus moves to multi-user access or requires remote access from non-Windows devices, reconsider personal M365 + SharePoint.

---

## 2026-05-07 — Python 3.12 pinned for MFIP venv

**Decision:** MFIP runs on Python 3.12.10 in a dedicated virtual environment at `C:\MFIP\repo\.venv\`. System Python (3.13.5) is left untouched and may be used for other projects.

**Reasoning:** Python 3.13 lacks mature wheels for several MFIP dependencies as of early 2026 — notably PyTorch (required by FinBERT/transformers), camelot-py (PDF table extraction), and blpapi (Bloomberg API). 3.12 is the highest version with full ecosystem support for the entire stack.

**Implication:**
- All `pip install` commands run inside the activated venv.
- `requirements.txt` will be the canonical package list.
- When invoking Python scripts in production scripts or Power Automate flows, the venv Python must be used explicitly: `C:\MFIP\repo\.venv\Scripts\python.exe`.

**Revisit trigger:** When PyTorch and blpapi ship full 3.13 wheels (likely mid-to-late 2026), reconsider upgrading. Not before.

---

## 2026-05-07 — Bloomberg integration: pull-and-cache, not live

**Decision:** MFIP does not run live Bloomberg queries during analysis. Bloomberg data is pulled in batch sessions on-site at Kingston University trading lab, exported to portable formats (CSV/Parquet/JSON), and ingested into MFIP's local data layer afterward. Phase 3 of the build sequence is split into 3a (on-site pull scripts) and 3b (off-site ingestion layer).

**Reasoning:** Bloomberg Terminal access is only available at Kingston's trading lab. Most build and analysis time happens off-site. A live-query architecture would block the system whenever Magnus is away from the lab. The pull-and-cache pattern matches how real institutional systems work — they warehouse data rather than re-query Bloomberg per analysis.

**Implication:**
- Phase 3a: Bloomberg pull scripts run on the trading lab machine, output to a portable export format. Magnus carries exports back via USB or cloud.
- Phase 3b: Local ingestion layer reads exports and loads them into MFIP's data store.
- `yfinance` is used for any data point that doesn't strictly require Bloomberg quality (live prices for the dashboard, intraday updates for the portfolio view).
- The Time Machine Controller (v2 backlog) will operate on cached historical data, not on live Bloomberg queries.
- Affects build sequence: `04_BUILD_SEQUENCE.docx` Phase 3 needs to be split into 3a/3b. Will update doc separately.

**Revisit trigger:** If Magnus gains a Bloomberg Anywhere subscription or other off-site Terminal access.

---

## 2026-05-07 — Bloomberg integration: Excel exports, market data only

**Decision:** Bloomberg data enters MFIP exclusively via manual Excel exports created at Kingston University's trading lab. The lab terminals are locked-down systems on which no software can be installed, so Python integration (`xbbg`, `blpapi`) is impossible. Magnus uses Bloomberg's native "Export to Excel" function, pastes values only (stripping live BBG formulas), and uploads the resulting `.xlsx` files to MFIP for ingestion.

Critically, Bloomberg's role is restricted to **market data only**. Bloomberg exports do not provide financial statements (income statement, balance sheet, cash flow) — those come from annual report PDFs via Extractor A. Bloomberg's normalized "FA" data diverges from as-filed statements by design (different fiscal alignment, different normalization rules, different segment taxonomy), making it unreliable as either a primary source or a cross-check.

**Reasoning:** This decision supersedes the earlier "pull-and-cache" entry from earlier today, which incorrectly assumed Python could be installed on the lab machines. It cannot. The Excel-export path is the only viable Bloomberg integration. Restricting Bloomberg to market data (prices, peer multiples, beta, consensus estimates, dividends) gives MFIP a clean architectural separation: PDFs are the source of truth for financial statements, Bloomberg provides the market-side data that filings cannot.

**Implication:**
- `xbbg` and `blpapi` removed from `03_TECH_STACK.docx`.
- Bloomberg Export Template (`07_BLOOMBERG_EXPORT_TEMPLATE.docx`) defines the seven required sheets, file naming, and export checklist.
- The folder `C:\MFIP\bloomberg_inbox\` is the drop zone for exported files.
- `openpyxl` (already in stack) handles all parsing.
- Sheet naming convention is provisional in v1 — confirmed at first lab session, then locked in for v2.
- Bloomberg `FA` function moved to "Out of Scope for V1" in the export template.

**Revisit trigger:** If Bloomberg Anywhere subscription becomes available, reconsider only after evaluating whether added complexity is worth it given Excel path works.

---

## 2026-05-07 — Valuation methodology expanded to DCF + Residual Earnings + DDM

**Decision:** MFIP's Modelling Layer (Layer 4) replaces the single "DCF Agent" with three sibling valuation agents: DCF Agent (free cash flow discounted at WACC), RE Valuation Agent (Penman residual earnings on reformulated statements), and DDM Agent (Gordon growth and multi-stage dividend discounting). Chief Analyst triangulates across all three intrinsic-value methods plus Comps, with Shock Analysis as the downside floor.

**Reasoning:** Magnus's MSc Finance programme (BA7007 Financial Statement Analysis at Kingston) trains the Penman tradition — reformulated statements, residual earnings, clean surplus accounting. His existing Clarkson PLC FSA workbook demonstrates fluent application of all three methods. Limiting MFIP to DCF only would strip out the most pedagogically valuable analytical content. Real institutional research triangulates across multiple valuation methods rather than committing to one — when methods converge, confidence is high; when they diverge, that divergence is itself analytical signal.

**Implication:**
- `02_AGENT_DESCRIPTIONS.docx` needs a major update (Session B): DCF Agent split into three sibling agents, Chief Analyst's triangulation logic significantly expanded.
- `01_ARCHITECTURE.docx` Layer 4 description updated to list six modelling agents (DCF, RE, DDM, FSA, Comps, Shock) instead of four.
- `04_BUILD_SEQUENCE.docx` Phase 6 expands — three valuation agents instead of one — and Phase 7 Chief Analyst gets richer triangulation logic. Time estimates increase accordingly.
- FSA Agent's Penman reformulation output (Reformulated IS, Reformulated BS) becomes a hard prerequisite for RE Valuation Agent.
- Method applicability rules: DDM excluded for non-dividend-paying companies. DCF universally applicable. RE Valuation requires reformulated statements (always available since FSA Agent runs first).
- Chief Analyst confidence calibration: HIGH if all applicable methods within ±15%, MEDIUM if ±25%, LOW if wider divergence (and Chief Analyst must diagnose why).
- These doc changes apply in Session B, not in this commit.

**Revisit trigger:** If a fourth valuation method becomes relevant to coverage universe (e.g., real options for resource extractors, EVA for capital-intensive sectors), evaluate adding as a new sibling agent.

---

## 2026-05-07 — Bloomberg Export Template as the ingestion contract

**Decision:** A formal document, `07_BLOOMBERG_EXPORT_TEMPLATE.docx`, defines the contract between Magnus's Bloomberg export sessions and MFIP's ingestion layer. The template specifies seven required sheets per company file (HP_Monthly, HP_Daily, Index_HP_Monthly, DVD, BETA, EE, RV_Comps), a strict filename convention (`<TICKER>_<YYYY-MM-DD>.xlsx`), an export session checklist with inline rename instructions, and quarantine conditions for non-conforming files. The ingestion layer (Phase 3) validates incoming files against this template — files that do not conform are quarantined or flagged with a clear validation error rather than silently producing garbage data.

**Reasoning:** Manual Excel exports are inherently variable in layout and quality. Without a strict template, every export session produces slightly different files and the ingestion layer becomes a fuzzy-matching nightmare. With a strict template, exports are predictable, the parser is simple, and Magnus has a written checklist to follow at the lab. The cost is a few minutes of disciplined naming when saving files; the benefit is robust ingestion forever after.

**Implication:**
- Phase 3 ingestion layer validates incoming files against the template before parsing.
- Magnus's pre-export checklist becomes part of the standard MFIP workflow at the trading lab. Estimated session time: ~20 minutes per company initially, ~12 minutes once familiar.
- Sheet naming convention is provisional pending first lab session — soft-validation only in v1, tightening to auto-quarantine in v2 once BBG's actual export naming is confirmed.
- Future companies added to coverage universe automatically inherit the template — no per-company customization needed.

**Revisit trigger:** First lab session (to confirm sheet naming convention against BBG defaults). Subsequently, when BBG meaningfully changes its export format (rare), or when a new BBG function is needed.
