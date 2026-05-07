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
