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

---

## 2026-05-07 — Session B complete: design docs aligned to DCF + RE + DDM methodology

**Decision:** Three design documents have been regenerated and uploaded to the project knowledge base, replacing the previous versions:

- `02_AGENT_DESCRIPTIONS.docx` — fully expanded to all 19 agents with Role, Inputs, Outputs, Key Behaviour, Failure Mode, and Prompt Guidance Seed for each. The single DCF Agent has been split into three sibling intrinsic-value agents (DCF Agent #10, RE Valuation Agent #11, DDM Agent #12). Chief Analyst (#15) rewritten with full triangulation logic: method-applicability filter, convergence-based confidence (±15% HIGH, ±25% MEDIUM, wider LOW), default weighting (35% DCF, 35% RE, 20% DDM, 10% Comps, Shock as downside floor), and explicit divergence-diagnostic patterns. New methodology appendix included.

- `01_ARCHITECTURE.docx` — Layer 4 updated to list six modelling agents (FSA, DCF, RE Valuation, DDM, Comps, Shock). Data Flow paragraph rewritten to reflect FSA-first ordering (because RE depends on reformulated statements), then three intrinsic-value agents in parallel with Comps, then Shock. Bloomberg-scope callout added. Key constraints list expanded.

- `04_BUILD_SEQUENCE.docx` — Phase 0 status reflects what's complete (Stage 0.1 done). Phase 3 rewritten as Bloomberg Ingestion Layer referencing the export template. Phase 6 expanded to ~10-14 hours with six explicit build steps in correct order. Phase 7 Chief Analyst expanded with triangulation, applicability filter, and confidence calibration steps. V2 phases section added.

**Reasoning:** These docs needed to align with the methodology decision logged earlier today. Without alignment, the agent descriptions doc (which is the spec the modelling code will be written against) would not match the architectural intent, leading to drift during Phase 6 build.

**Implication:**
- Phase 6 estimate increased from ~6-8 hours (single DCF) to 10-14 hours (three valuation agents + FSA + Comps + Shock).
- FSA Agent's reformulated statements (Reformulated_IS, Reformulated_BS) are now an explicit hard prerequisite for RE Valuation Agent — captured in agent descriptions and architecture constraints.
- Agent prompt seeds in `02_AGENT_DESCRIPTIONS.docx` are the starting points for system prompts when each agent is built. Expand at build time, do not improvise from scratch.
- Chief Analyst's default weighting (35/35/20/10) should be revisited after first 30 recommendations, when Learning Agent data accumulates in v2.

**Revisit trigger:** After v1 has produced 30+ recommendations and Learning Agent activates in v2, evaluate whether the default weighting needs calibration. The current weighting reflects Magnus's Penman-heavy methodology preference; data may suggest different weights.

---

## 2026-05-07 — Stage 0.2 complete: Python dependencies pinned and smoke-tested

**Decision:** Phase 0 Stage 0.2 complete. Python environment fully provisioned per `03_TECH_STACK.docx`, with pinned manifests and an automated environment smoke test.

- `requirements.txt` created at repo root with range-pinned dependencies (e.g. `pandas>=2.2,<3.0`). 14 direct dependencies covering all v1 needs: numerical stack, market/macro data, DuckDB, Dash + AG Grid, document/spreadsheet generation, and PDF extraction.
- `requirements.lock.txt` generated via `pip freeze` capturing 68 exact pins (direct + transitive) for reproducibility.
- `scripts/smoke_test_env.py` created. Imports all 14 v1 packages, runs a DuckDB in-memory query, and instantiates a Pydantic BaseModel. Exits 0 on full pass, 1 on any failure.
- All 16 smoke-test checks passing on Python 3.12.10. Notable resolved versions: pandas 2.3.3, numpy 2.4.4, scipy 1.17.1, pydantic 2.13.4, duckdb 1.5.2, dash 3.4.0, camelot-py 1.0.9, pymupdf 1.27.2.3.
- Committed as `a258675` on `main`.

**Reasoning:** Pinning via `requirements.txt` (curated ranges) plus `requirements.lock.txt` (exact freeze) gives both readability and reproducibility. Any future machine can reproduce the exact stack via `pip install -r requirements.lock.txt`. The smoke test is the acceptance criterion for environment health -- it runs in under 3 seconds and catches any silent install corruption before it bites a downstream phase.

**Implication:**
- `transformers` and `torch` (FinBERT for News Agent) deferred to Stage 5.0. Adds ~2.5 GB and a CUDA/CPU decision unnecessary for Phases 0-4. Commented in `requirements.txt` for visibility.
- Ghostscript binary (Camelot's PDF backend) deferred to Phase 4 start. The Python `camelot-py` package installed cleanly; the system-level Ghostscript only matters when we actually run PDF extraction.
- `--break-system-packages` flag in `03_TECH_STACK.docx` is irrelevant inside an activated venv on Windows. Worth correcting in that doc next time it is edited so a future re-provisioning does not get confused.
- `opencv-python-headless` was pulled in instead of full `opencv-python` (Camelot's `[cv]` extra). Preferable for a non-GUI use case -- smaller install, no display dependencies.
- numpy 2.4.x resolved cleanly across the stack. Worth re-running the smoke test if any package is upgraded later, since NumPy 2.x compatibility issues do still surface in some scientific-Python edges.

**Revisit trigger:** Re-run `scripts/smoke_test_env.py` after every dependency upgrade, before the corresponding phase begins, and whenever the venv is rebuilt on a new machine. If any check fails, do not proceed with the affected phase until resolved.

---

## 2026-05-07 — Phase 0 closeout (item 1): GitHub remote configured

**Decision:** Local repo at `C:\MFIP\repo` pushed to a new private GitHub remote at `https://github.com/MagnusThomassen/mfip`. All 7 commits and 25 objects on `main` now mirrored to GitHub. `origin/main` set as upstream for local `main`.

- Auth method: GitHub CLI (`gh` 2.92.0) via HTTPS + browser device flow. Credentials persisted in Windows Credential Manager — no token to manage manually, no SSH key generated.
- Repo created with `gh repo create mfip --private --source=. --remote=origin`. Visibility verified Private in browser. Description set to "Magnus Financial Intelligence Platform - personal equity analysis system (private)".
- `.venv/` correctly excluded from push (verified via GitHub file listing) — `.gitignore` from Stage 0.1 is working as intended.

**Reasoning:** Private repo is mandatory because the methodology, agent prompt seeds, and decisions log together represent the analytical IP of the project. GitHub CLI was chosen over SSH keys or PAT because (a) browser auth is the lowest-friction setup on a fresh Windows machine, (b) credentials are managed by Windows itself rather than a file Magnus has to protect, and (c) `gh` becomes available for future operations like creating issues, PRs, or a `logs-archive` branch from the terminal without context switching. The trade-off is one extra tool installed; the benefit is that future GitHub-side operations are scriptable from PowerShell.

**Implication:**
- All future commits should be pushed regularly. Phase 0 work to date had no off-machine backup — that gap is now closed.
- The `logs-archive` branch referenced in Phase 2 (nightly JSON log export, `04_BUILD_SEQUENCE.docx`) can be created and pushed as a separate branch when Phase 2 begins. No action required in Phase 0.
- Repo description currently says "personal equity analysis system" — sufficient for now. A proper `README.md` is deferred until there is something user-facing to describe (likely after Phase 1 dashboard shell is buildable).
- `gh` CLI install added GitHub.cli to system PATH. Future PowerShell sessions will see `gh` natively without the manual `$env:Path` refresh used in this session.

**Revisit trigger:** If Magnus moves to a second development machine, repeat `gh auth login` on that machine to register credentials. If repo ever needs to be made public (e.g. for a portfolio piece in a job application), re-evaluate whether the decisions log and methodology should be sanitised first.

---

## 2026-05-07 — Phase 0 item 2: Finance plugins installed via Claude Code CLI 2.1.132

**Decision:** Installed `financial-analysis` (core) and `equity-research` plugins from the `claude-for-financial-services` marketplace (source repo: `anthropics/financial-services-plugins` on GitHub). Skipped `investment-banking`, `private-equity`, and `wealth-management` as out of scope for MFIP. The earlier-doc plugin names `model-builder` and `valuation-reviewer` do not exist in the current marketplace — their capabilities (DCF, comps, 3-statement models) are bundled inside the `financial-analysis` core plugin.

**Reasoning:** The finance plugins are skill scaffolding for Claude Code itself — slash commands like `/dcf`, `/comps`, `/ic-memo` and bundled skill files. They are not runtime dependencies of MFIP and nothing in the agent pipeline imports them. Two plugins covers MFIP's actual scope (equity research and FSA-style modelling) without dragging in IB, PE, or wealth-management verticals that have no place in this project. The marketplace's declared name (`claude-for-financial-services`) differs from the GitHub repo name (`financial-services-plugins`); install commands must use the declared name.

**Implication:**
- Both plugins shipped with a `hooks.json` containing `[]`, which fails the CLI's schema validator on Claude Code 2.1.132 (the schema expects an object with a required `hooks` record). Patched both files locally to `{"hooks": {}}` to unblock loading:
  - `C:\Users\MagnusThomassen\.claude\plugins\cache\claude-for-financial-services\financial-analysis\0.1.0\hooks\hooks.json`
  - `C:\Users\MagnusThomassen\.claude\plugins\cache\claude-for-financial-services\equity-research\0.1.0\hooks\hooks.json`
- `03_TECH_STACK.docx` plugin install commands corrected: marketplace suffix is `@claude-for-financial-services`, not `@financial-services-plugins`; only the two relevant plugins are listed.
- `04_BUILD_SEQUENCE.docx` Phase 0 item 2 ticked off.
- Environment note for future threads: Claude Code CLI on Windows is the install surface. The Claude.ai project chat (where most architecture work happens) does not expose `/plugin` or `/setup-cowork` slash commands, so plugin install cannot happen from inside a project chat session.

**Revisit trigger:** If `claude plugin update` or `claude plugin marketplace refresh` re-pulls the cache from upstream, the `[]` `hooks.json` will return and both plugins will fail to load again — re-apply the `{"hooks": {}}` patch. Periodically (monthly) check `github.com/anthropics/financial-services-plugins` for an upstream fix; once the published `hooks.json` is valid, this entry can be marked resolved.

---

## 2026-05-07 — Power Automate dropped from architecture; replaced with Python + Task Scheduler + Gmail SMTP + structured alerting

**Decision:** Power Automate (Cloud and Desktop) is removed from MFIP's architecture entirely. The "Logistics Layer" specified in `01_ARCHITECTURE.docx` is replaced by three native components:

1. **File watching and folder monitoring** → Python `watchdog` library, run as Windows scheduled tasks. Replaces PA Desktop flows for `bloomberg_inbox\` and `filings\` monitoring.
2. **Scheduled jobs** (nightly log archive, weekly digest, Git commits of log exports) → Windows Task Scheduler invoking Python scripts. Replaces all PA Cloud time-triggered flows.
3. **Notifications** → Gmail SMTP from `magnus.thomass1@gmail.com` (sender) to `magnus.t@live.no` (recipient), with structured alert payloads, local disk fallback for delivery failures, and a dashboard surface for unsent items. Replaces PA Cloud Teams cards and Outlook digest emails.

The dashboard remains the canonical state of the system. All approval workflows (portfolio rebalancing, Critical security remediation) happen inside the dashboard — there is no external approval surface in v1.

**Reasoning:** The original Power Automate architecture was aspirational rather than well-suited. Several factors converged:

- **No viable Microsoft account.** Personal M365 was already rejected (`2026-05-07 — Storage layer` decision: ~£60/year deemed unnecessary). University and work accounts both have policy restrictions and lifecycle dependencies (Kingston account dies at graduation; running personal projects on an employer tenant is a policy issue). Free personal Microsoft accounts have heavily restricted PA Cloud connectors. There is no good account answer.
- **PA was being asked to do too much.** Of the eight PA tasks specified in `01_ARCHITECTURE.docx`, only two (Teams notifications, approval workflows) genuinely benefited from PA-shaped capabilities, and both depended on Teams access that the account situation above precludes anyway. The other six (file watching, log archiving, model archival, news aggregation, weekly digest, scheduled jobs) are simpler in Python.
- **Architectural inconsistency.** MFIP's whole identity is "every decision traceable, version-controlled, reproducible." PA flows live in a Microsoft cloud account, GUI-edited, not Git-diffable. Half the system in Python and half in PA flows would have meant half the system was outside the version-control envelope. That's a bad split for a project with this design philosophy.
- **GUI dependency.** PA Desktop has to be running on the Windows machine for local file watching to work. A Python `watchdog` script can run as a background service or scheduled task without a GUI, with no "did I remember to launch PA Desktop today" failure mode.
- **The notification trade-off was theoretical.** The one capability PA-via-Teams might have offered — push-notification approval cards — was never actually accessible given the account situation. Dropping PA loses no real capability.

**Implication:**

***Architecture changes (require doc updates in next session):***

- `00_PROJECT_OVERVIEW.docx` Guiding Principle #6 ("Power Automate Handles Logistics, Claude Handles Intelligence") becomes **"Python Handles Logistics, Claude Handles Intelligence."**
- `01_ARCHITECTURE.docx` "Logistics" row in the layer summary table is rewritten. The full "POWER AUTOMATE RESPONSIBILITIES" table is replaced with a "PYTHON LOGISTICS LAYER" table covering the three pillars below.
- `03_TECH_STACK.docx` removes "Logistics automation" (PA), "Notifications" (Teams connector). Adds: `watchdog` for file events, `python-dotenv` for secret management, standard library `smtplib` and `email` for SMTP. Notes Windows Task Scheduler as the native scheduling layer.
- `04_BUILD_SEQUENCE.docx` Phase 0 item 3 ("Configure Power Automate connectors") is removed entirely. Phase 2 (Logging Infrastructure) absorbs the new alert-delivery design as part of the same logging layer. References to PA in Phases 3, 7, and 8 are rewritten.
- `05_DASHBOARD_SPEC.docx` rebalancing approval banner becomes the *primary* approval surface (it was previously framed as a mirror of a Teams card). New element: "unsent alerts" indicator in Zone 1 (Command Centre) showing count of alerts that failed to deliver and are queued in `unsent_alerts/`.
- `06_SECURITY_COUNCIL.docx` references to "Teams + email" notification channels become "Gmail SMTP + dashboard banner."
- `07_BLOOMBERG_EXPORT_TEMPLATE.docx` references to PA Desktop watching the inbox stay conceptually correct (something watches the folder), implementation note updated to `watchdog` script.

***Implementation: pillar 1 — file watching (`watchdog`):***

- One Python script per watched folder. Initial set: `bloomberg_inbox\`, `filings\`. Each script registers a `watchdog` Observer on its folder, fires a handler when a new `.xlsx` (Bloomberg) or `.pdf` (filings) lands, validates the file against its template, and queues it for the appropriate downstream agent.
- Scripts run as scheduled tasks via Windows Task Scheduler with trigger "At log on" + restart-on-failure. They are NOT user-launched processes — they survive reboots and run silently.
- Scripts log every file event to `decision_log` (Phase 2 logging infrastructure) so the file ingestion pipeline is fully auditable.

***Implementation: pillar 2 — scheduled tasks (Task Scheduler):***

- Nightly log export: scheduled task at 02:00 invokes a Python script that exports new `decision_log` and `security_log` entries since the last export to `C:\MFIP\logs\exports\<date>.json`, then commits the new file to the `logs-archive` branch on Git.
- Weekly digest: scheduled task at 07:00 every Monday invokes a Python script that summarises the past week's pipeline activity (companies analysed, alerts raised, recommendations issued) and sends it as a single email via the alerting pillar.
- All scheduled tasks are defined in PowerShell scripts committed to `scripts/scheduled_tasks/` so they can be re-applied to a new machine via `./register_tasks.ps1`.

***Implementation: pillar 3 — structured alerting (Gmail SMTP):***

- Single Python module `mfip_alerts.py` (target ~150 lines) implementing three concerns:
  1. **`Alert` Pydantic model** — schema for any alert. Fields: `correlation_id` (UUID, ties alert to pipeline run, matches `decision_log`/`security_log`), `timestamp` (ISO 8601 UTC), `severity` (Advisory/Warning/Critical), `issuing_agent`, `title`, `summary`, `error_class` (optional), `error_message` (optional), `stack_trace` (optional, truncated to ~30 lines), `context_fields` (dict — company, fiscal year, document path, etc.), `recommended_action` (optional), `dashboard_link` (deep-link to Zone 2 with company pre-selected).
  2. **`render_alert(alert: Alert)`** — produces a multipart MIME email (HTML primary, plain-text fallback). HTML is severity-color-coded (red Critical, amber Warning, yellow Advisory). Plain-text is a clean structured fallback for clients that don't render HTML.
  3. **`send_alert(alert: Alert)`** — attempts SMTP send; on any failure, writes the alert payload to `C:\MFIP\runtime\unsent_alerts\<timestamp>_<correlation_id>.json`. Either way, also writes an entry to `security_log` recording the alert and its delivery status.
- **Self-contained alerts principle:** every alert email is debuggable from its body alone. Magnus should not need to grep logs or remember context to understand what an alert is telling him. The Pydantic model is designed with this in mind — context, error details, and remediation are all first-class fields, not afterthoughts.
- **Local fallback:** when SMTP fails (network, Gmail throttling, app-password revoked), the alert is never lost. It goes to disk in `unsent_alerts/`. Next successful run of any send-alert path also drains the queue: scans the folder oldest-first, retries each, moves successful sends to `unsent_alerts/sent/<date>/` and leaves persistent failures in place.
- **Dashboard surface:** Zone 1 (Command Centre) shows a small "X unsent alerts" indicator when `unsent_alerts/` is non-empty. Clicking opens a queue view. This means an alert can never be silently lost — it's either in `magnus.t@live.no`, on disk, or visible in the dashboard.

***Heartbeat — interface in v1, watchdog process in v1.5:***

- The orchestrator (Agent 01) touches `C:\MFIP\runtime\orchestrator.heartbeat` every 60 seconds while running. This is a v1 requirement — approximately 5 lines in the orchestrator's main loop.
- The watchdog **process** that monitors the heartbeat file and emails an alert when its mtime exceeds 5 minutes is **deferred to v1.5**. v1 is hands-on use where Magnus is at the dashboard daily and a missed crash is a "lost morning of progress" inconvenience, not a "lost data" failure mode. The watchdog becomes meaningful when MFIP is run unattended.
- By committing to the heartbeat *interface* now, the watchdog process can be added in v1.5 without touching v1 code. The integration point is locked in; the consumer is scheduled.

***Credentials and secrets:***

- Gmail App Password generated for `magnus.thomass1@gmail.com` (requires 2-Step Verification on that account first).
- Stored at `C:\MFIP\repo\.env` as `MFIP_GMAIL_APP_PASSWORD=...`, `MFIP_GMAIL_SENDER=magnus.thomass1@gmail.com`, `MFIP_GMAIL_RECIPIENT=magnus.t@live.no`.
- `.env` added to `.gitignore` (verify before first commit of the alerting module).
- Loaded via `python-dotenv` (added to `requirements.txt` next time it's edited).
- Future secrets (NewsAPI key, etc.) follow the same pattern — `.env` is the canonical secret store.

***What is NOT being built in v1:***

- No external notification surface other than email. No Discord, no Telegram, no SMS. If email proves insufficient in practice, revisit then.
- No mobile-friendly approval webpage. Approvals require opening the dashboard.
- Heartbeat watchdog process is v1.5 (the heartbeat file itself is v1; see above).

**Affected docs:** `00_PROJECT_OVERVIEW.docx`, `01_ARCHITECTURE.docx`, `03_TECH_STACK.docx`, `04_BUILD_SEQUENCE.docx`, `05_DASHBOARD_SPEC.docx`, `06_SECURITY_COUNCIL.docx`, `07_BLOOMBERG_EXPORT_TEMPLATE.docx` — all require updating in a dedicated doc-revision session before Phase 1 build begins. Until those updates land, this decisions.md entry is the canonical reference and supersedes any PA-related guidance in those documents.

**Revisit trigger:**

- If after 4+ weeks of v1 use, email proves insufficient (alerts missed, latency too high, inbox noise unmanageable) — revisit notification surface, with Discord webhook or ntfy.sh as next-best options.
- If MFIP transitions from hands-on use to unattended/daemon-like operation — promote the heartbeat watchdog from v1.5 to immediate priority.
- If multi-user access ever becomes a requirement — revisit the whole "Python + Task Scheduler" stack, since it's single-machine by design.
- If Anthropic ships a Claude-native scheduling/notification primitive that subsumes parts of this layer — revisit whether to migrate.
- Annual review: re-evaluate whether the Gmail account is still the right sender. If the account changes or 2SV gets disabled, alerting silently breaks.

## 2026-05-08 — Doc-revision pass complete: design docs aligned with Python logistics architecture

**Decision:** All eight design documents affected by the 2026-05-07 "Power Automate dropped from architecture" decision have been updated and re-uploaded to the project knowledge base. The design docs are now in alignment with the architectural state captured in decisions.md — decisions.md no longer supersedes the design docs on PA, Python logistics, Gmail SMTP, or the Orchestrator heartbeat.

**Docs updated this session:**
- `00_PROJECT_OVERVIEW.docx` — Guiding Principle #6 renamed and rewritten ("Python Handles Logistics, Claude Handles Intelligence"). Glossary unchanged (no PA entry existed).
- `01_ARCHITECTURE.docx` — Layer Summary "Logistics" row rewritten. Data Flow paragraph updated to reference Python `watchdog` script. Key Architectural Constraints list extended with the Orchestrator heartbeat interface commitment. The full "POWER AUTOMATE RESPONSIBILITIES" section replaced with "PYTHON LOGISTICS LAYER" — three-pillar table covering file watching, scheduled jobs, and structured alerting, plus an APPROVAL SURFACE callout.
- `02_AGENT_DESCRIPTIONS.docx` — Agent 01 Orchestrator: heartbeat bullet added to Key Behaviour, "Power Automate" replaced with "filings watcher" in Inputs. Agent 06 News Agent: RSS aggregation reattributed from PA to the News Agent itself. Agent 19 Chief Security Agent: Warning-level delivery channel updated from "Teams + email + dashboard" to "Gmail SMTP + dashboard banner."
- `03_TECH_STACK.docx` — Stack Overview table: removed PA + Teams rows, added watchdog, Task Scheduler, smtplib/email, python-dotenv. Python Environment Setup section: rewritten to assume activated venv, removed the irrelevant `--break-system-packages` flag, added `pip install watchdog python-dotenv`. Power Automate Connectors section deleted entirely. New Tool Selection Rationale subsection "Why Python Logistics over Power Automate?" added.
- `04_BUILD_SEQUENCE.docx` — Phase 0 status callout updated to reflect closeout (all four items checked, PA item recorded as removed). Phase 0 checklist: PA item deleted entirely, commit references added to closeout items. Phase 2 absorbs the new alert-delivery design (`mfip_alerts.py` build step + nightly Task Scheduler log export). Phase 3 Bloomberg Ingestion: PA Desktop replaced with Python `watchdog` script. Phase 5 Intelligence Layer: PA RSS aggregation replaced with feedparser-based News Agent aggregation. Phase 7: PA approval workflow replaced with in-dashboard Zone 4C banner. Phase 8: warning card formatter scope clarified to produce both dashboard banner content and the structured `Alert` payload for `mfip_alerts.py`.
- `05_DASHBOARD_SPEC.docx` — Zone 1 Command Centre: new "Unsent Alerts indicator" element added between Alert Badges and Company Selector. Zone 4C Rebalancing Alert Banner: framed as primary approval surface in v1, with persistence-until-actioned semantics. Real-Time Update Schedule table: News feed source updated from PA push to News Agent poll.
- `06_SECURITY_COUNCIL.docx` — Warning level delivery channel updated to Gmail SMTP + dashboard banner with sender/recipient addresses. Audit trail backup mechanism rewritten from SharePoint to nightly local export + commit to logs-archive Git branch.
- `07_BLOOMBERG_EXPORT_TEMPLATE.docx` — confirmed no-op. The template was originally written at an implementation-agnostic abstraction level and required no changes.

**Reasoning:** Without this alignment, the design docs and decisions.md would have continued to disagree on PA/Python/Gmail SMTP, with decisions.md as the canonical reference and the design docs out of date. Phase 1 build (dashboard shell) needs to start from a clean, internally consistent document set.

**Implication:**
- decisions.md no longer supersedes the design docs on PA-related guidance — they are now in alignment.
- Phase 0 status reflected in `04_BUILD_SEQUENCE.docx`: "Phase 0 complete; ready for Phase 1."
- One follow-up identified during the session, not closed: `feedparser` was added to `04_BUILD_SEQUENCE.docx` Phase 5 as the RSS library but has not been added to `03_TECH_STACK.docx`. Trivial library; can be added the next time the tech stack doc is touched, or picked up at Phase 5 build start.
- The known design-doc/Git gap remains unsolved (design docs live only in the project KB, not in Git). Out of scope for this session per the session brief.

**Affected docs:** `00_PROJECT_OVERVIEW.docx`, `01_ARCHITECTURE.docx`, `02_AGENT_DESCRIPTIONS.docx`, `03_TECH_STACK.docx`, `04_BUILD_SEQUENCE.docx`, `05_DASHBOARD_SPEC.docx`, `06_SECURITY_COUNCIL.docx`, `07_BLOOMBERG_EXPORT_TEMPLATE.docx`. All updated 2026-05-08 (or confirmed no-op).

**Revisit trigger:** None for this entry — it's a closeout. The architectural decisions that drove it (Power Automate dropped, Python logistics adopted) carry their own revisit triggers in their respective decisions.md entries.

## 2026-05-08 — Bloomberg export: USD standardisation and FX source

**Decision part 1 — Display currency:**
All Bloomberg exports run with Excel display currency set to USD,
with one exception: the BETA function, which retains its default
behaviour (regression in local currency against local index).

**Affected sheets:** HP_Monthly, HP_Daily, Index_HP_Monthly, DVD, EE, RV_Comps
**Not affected:** BETA (local currency preserved for correct regression)

**Reasoning:**
1. Reduces manual configuration per session from 6 settings (one per
   company) to 1 — fewer error sources, faster export.
2. USD is Bloomberg's default — least friction with Terminal behaviour.
3. Cross-border comps and portfolio aggregation require a common
   currency for reconciliation regardless. Standardisation at the
   source is cleaner than conversion at use.
4. MSFT — the only USD-listed company in the universe — requires
   no conversion at all.

**Decision part 2 — FX source:**
Historical FX rates are pulled from Bloomberg (HP on FX crosses) as
part of the same export session as company and index data.
`pandas-datareader` remains in the stack for live FX in the dashboard
(intraday display only) but is NOT the source of historical rates
used by the modelling layer.

**FX crosses exported (v1 universe):**
- `NOKUSD Curncy` — for EQNR, DNB, TEL
- `DKKUSD Curncy` — for NOVO B
- `GBPUSD Curncy` — for CKN
- USD/USD not required (MSFT is native USD)

All FX exports: HP, monthly periodicity, 10-year range — same
resolution as Index_HP_Monthly.

**Reasoning for BBG as FX source (not pandas-datareader):**
1. Temporal consistency — FX rates carry the same export timestamp
   as company and index data. No drift between data sources.
2. One data source, one failure mode. If a BBG export is missing,
   the ingestion layer knows immediately that the package is incomplete.
3. Parser symmetry — FX sheets follow the same HP format as the
   other price-history sheets. No new parser path required.
4. pandas-datareader rates can diverge from BBG rates (different
   underlying sources, different times of day). Mixing them creates
   subtle reconciliation problems that are difficult to detect.

**FX handling in the ingestion layer remains necessary:**
- Annual report PDF data arrives in the company's reporting currency
  (NOK/DKK/GBP/USD) and cannot be changed at the source.
- The ingestion layer tags BBG data as USD, tags PDF data with native
  currency derived from the ticker exchange suffix, and maintains an
  FX table from the three FX exports for conversion at reconciliation
  time.
- Conversion happens at use, not at storage — the Verified Dataset
  retains native values for full audit trail.

**BETA exception:**
Beta regression must be performed in local currency against the local
benchmark index to remain methodologically correct (EQNR vs OBX in
NOK, not both converted to USD). BBG's BETA function handles this
internally provided display currency is not manipulated before export.
Documented explicitly in `07_BLOOMBERG_EXPORT_TEMPLATE.docx` checklist.

**Open question — FX snapshot selection at use time:**
This decision establishes that FX rates are stored as a series of
point-in-time exports. It does NOT yet specify which snapshot the
modelling layer uses when reconciling a specific PDF figure with
a specific BBG figure. Three viable rules:

1. **Most recent snapshot at analysis time** — simplest rule. Risk:
   when reconciling a 2024 annual report against current BBG data,
   uses today's FX rate, not the FX rate that was relevant when the
   PDF was published. Acceptable for live analysis, problematic for
   any historical comparison.

2. **Snapshot matching PDF publication date** — most temporally
   correct for reconciling against filed financial statements. Each
   PDF figure is converted at the FX rate that prevailed when that
   PDF was published. Adds a lookup step but produces the cleanest
   reconciliation.

3. **Daily time-series interpolated per analysis date** — most flexible
   for arbitrary historical analysis. Required for v2 backtesting.
   Overkill for v1 use cases.

**Provisional default for v1:** Rule 2 (snapshot matching PDF publication
date) for reconciling PDF-sourced figures with BBG market data, falling
back to Rule 1 (most recent) when PDF publication date is unavailable
or when the figure is BBG-native (peer multiples, prices). This balances
correctness with simplicity. The decision is not final until Phase 4
(FSA Agent build) — it will be confirmed or revised when the first
real reconciliation is implemented against EQNR's 2024 annual report.

This open question is flagged as a TODO in `04_BUILD_SEQUENCE.docx`
Phase 4 so it is not silently absorbed during implementation.

**Affected docs:**
- `07_BLOOMBERG_EXPORT_TEMPLATE.docx` — Currency handling section,
  pre-export checklist, BETA function checklist line, quarantine
  conditions table, and a new FX EXPORTS section with filename
  convention.
- `04_BUILD_SEQUENCE.docx` — Phase 3 ingestion layer must validate
  presence of FX exports against the company universe (e.g., if any
  Norwegian ticker is in the package, NOKUSD must also be present).
  Phase 4 must include a TODO referencing the FX snapshot selection
  rule above. Phase time estimates unchanged — FX parsing reuses the
  HP parser path.

**Revisit triggers:**
- If MFIP expands the universe with companies in additional currencies
  (JPY, CHF, CAD, SEK), add new FX crosses to the export package and
  update the ingestion validator's required-FX list.
- If Magnus introduces a base-currency selector in the dashboard in v2,
  reconsider whether standardisation should move from the export layer
  to the ingestion layer.
- If pandas-datareader proves to have better historical coverage than
  BBG for specific dates, source prioritisation may be revised.
- **Phase 4 build trigger:** confirm or revise the FX snapshot selection
  rule against the first real PDF-vs-BBG reconciliation (EQNR 2024).
  Update this entry with the final decision.

## 2026-05-08 — Logistics-layer dependencies pinned and smoke-tested

**Decision:** The three logistics-layer Python packages flagged across
multiple earlier decisions but never formally pinned (`feedparser`,
`watchdog`, `python-dotenv`) have been installed, pinned in
`requirements.txt` under a new "Logistics layer" group, captured in
`requirements.lock.txt`, and added to the Stage 0.2 smoke test.

**Versions installed:**
- `feedparser==6.0.12` (with transitive `sgmllib3k==1.0.0`)
- `watchdog==6.0.0`
- `python-dotenv==1.2.2`

**Pinning ranges in requirements.txt:**
- `feedparser>=6.0,<7.0`
- `watchdog>=6.0,<7.0`
- `python-dotenv>=1.2,<2.0`

**Commits:**
- `7474a3f` — deps: add logistics-layer packages (watchdog, dotenv, feedparser)
- `d9a5ef2` — test: extend smoke test with logistics-layer packages

**Smoke test changes:**
- Total checks: 16 → 19.
- `importlib.metadata.version()` introduced as the version-lookup
  mechanism for `watchdog` and `python-dotenv`, since neither exposes a
  module-level `__version__` attribute. Pattern available for future
  packages with the same quirk.

**Reasoning:** These packages were referenced across `01_ARCHITECTURE.docx`,
`03_TECH_STACK.docx`, `04_BUILD_SEQUENCE.docx`, and the 2026-05-07
"Power Automate dropped" entry, but the formal pinning kept getting
deferred. Closing this thread now means a fresh clone of the repo
followed by `pip install -r requirements.lock.txt` will reproduce the
exact environment the smoke test validates — the property required
before Phase 1 build begins.

**Resolves:**
- 2026-05-07 "Power Automate dropped" entry (line 261): "python-dotenv
  added to `requirements.txt` next time it's edited" — done.
- 2026-05-08 doc-revision pass entry (line 299): "feedparser ... has
  not been added to `03_TECH_STACK.docx`" — partially done. Requirements
  side resolved here. Doc update to `03_TECH_STACK.docx` carried into
  the 2026-05-09 morning doc-revision session.

**Affected docs:**
- `requirements.txt` — new "Logistics layer" group added.
- `requirements.lock.txt` — regenerated, 68 → 72 pins.
- `scripts/smoke_test_env.py` — three new import checks, new
  `importlib.metadata` import.
- `03_TECH_STACK.docx` — pending update in 2026-05-09 morning session
  (Stack Overview table needs `feedparser` row; pip install line needs
  `feedparser` appended to existing `watchdog python-dotenv`).

**Revisit trigger:** When upgrading any of these three packages, re-run
the smoke test. If watchdog moves to 7.x or python-dotenv to 2.x, the
pinning ranges need a deliberate decision rather than an automatic bump.

---

## Carried into 2026-05-09 morning doc-revision session

Three documentation threads remain open from 2026-05-08 evening's
work. They are batched for a single focused session before the
Bloomberg lab visit:

1. **`03_TECH_STACK.docx`** — add `feedparser` to Stack Overview table
   and Python Environment Setup pip install line. Verify `watchdog`
   and `python-dotenv` rows from 2026-05-08 PA-removal pass are
   present.

2. **`07_BLOOMBERG_EXPORT_TEMPLATE.docx`** — five edits implementing
   the USD standardisation and FX-source decision (see 2026-05-08
   "Bloomberg export: USD standardisation and FX source" entry):
   - Pre-export checklist: USD-at-session-start
   - Per BBG function: BETA exception note + checklist line update
   - Currency handling section: full rewrite
   - Quarantine conditions table: new BETA-currency row
   - New FX RATE EXPORTS section between Required Sheets and Export
     Session Checklist

3. **`04_BUILD_SEQUENCE.docx`** — three additions:
   - Phase 3: FX-presence validator checklist item
   - Phase 4: `pdf_publication_date` field in ExtractionOutput schema
   - Phase 6: split FSA Agent step into reformulation + FX-snapshot-rule
     checkboxes

After the doc-revision pass, README.md "Last sync" date moves to
2026-05-09 and local working copies are refreshed from the project
knowledge base.

## 2026-05-09 — ANR Consensus added to Bloomberg export template

**Decision:** ANR (Analyst Recommendations) is added as a seventh required
sheet in each company workbook. Sheet name: ANR. BBG function: ANR on ticker.

**Reasoning:** The Dashboard Spec (05_DASHBOARD_SPEC.docx Zone 3D — Analyst
Consensus Tracker) specifies display of current consensus rating, buy/hold/sell
breakdown, and MFIP-vs-Street comparison. The existing EE sheet covers forward
EPS/revenue/EBITDA estimates but does not provide the rating distribution — that
gap was unresourced. ANR closes it. The Agent 06 (News Agent) description in
02_AGENT_DESCRIPTIONS.docx listed "analyst rating changes from Bloomberg EE
sheet" as an input, which was a misconception (EE is estimates, ANR is
recommendations) — this decision corrects the source. Marginal export cost at
the lab is ~30 seconds per company.

**Implication:**
- 07_BLOOMBERG_EXPORT_TEMPLATE.docx: ANR row added to Required Sheets table;
  ANR step added to Per BBG function checklist; count updated from six to seven
  sheets; Relationship to Modelling Agents table updated (News Agent + Chief
  Analyst consume ANR).
- 02_AGENT_DESCRIPTIONS.docx: Agent 06 News Agent inputs — "analyst rating
  changes from Bloomberg EE sheet" corrected to "Bloomberg ANR sheet". Deferred
  to next doc-revision session.
- 04_BUILD_SEQUENCE.docx: Phase 3 ingestion layer validates ANR sheet presence
  alongside the other six required sheets. Covered by Edit 3 this session.
- Session Execution Matrix: ANR column added as the 7th function per company row.

**Revisit trigger:** If ANR proves to have sparse coverage for any company in
the universe (some smaller tickers have few or no analyst ratings), flag as
Advisory in the ingestion layer rather than quarantining — missing ANR is
degraded functionality, not a data-integrity failure.

## 2026-05-09 — Doc-revision pass complete: Bloomberg template restructured, ANR added, Session Execution Matrix added, Build Sequence Phase 3 FX validator updated, Tech Stack feedparser row added

**Decision:** Three design documents updated in a focused pre-lab session.
All changes reflect decisions already logged in decisions.md — this entry
records the doc-revision pass itself.

**Docs updated this session:**
- `03_TECH_STACK.docx` — feedparser row added to Stack Overview table
  (pip install line already had it; table was missing the entry).
- `07_BLOOMBERG_EXPORT_TEMPLATE.docx` — major revision implementing the
  2026-05-08 USD standardisation and FX source decision: pre-export checklist
  updated (USD-once-per-session), BETA exception documented, Currency handling
  section rewritten, BETA-in-USD quarantine row added, Index_HP_Monthly removed
  from company sheets, new INDICES WORKBOOK and FX WORKBOOK sections added,
  FILE NAMING CONVENTION updated for three file families, ANR added as seventh
  required sheet, SESSION EXECUTION MATRIX added (8 files × 7 functions).
- `04_BUILD_SEQUENCE.docx` — Phase 3: stale single-sheet validation step
  replaced with three items covering company workbooks, INDICES workbook,
  and FX workbook validation including pandas-datareader fallback check and
  BETA currency detection.

**Deferred to next doc-revision session:**
- `02_AGENT_DESCRIPTIONS.docx` — News Agent input: "analyst rating changes
  from Bloomberg EE sheet" should be corrected to "Bloomberg ANR sheet".

**Affected docs:** `03_TECH_STACK.docx`, `07_BLOOMBERG_EXPORT_TEMPLATE.docx`,
`04_BUILD_SEQUENCE.docx` — all updated 2026-05-09.

**Revisit trigger:** None — this is a closeout entry.2026-05-08 — Automated filings acquisition flagged as v2 (Playwright held in reserve)
Decision: Automated annual-report PDF acquisition is added to V2_BACKLOG.docx as deferred component #5. V1 continues to use manual PDF drops to C:\MFIP\filings\<TICKER>\. When v2 work begins, the fetcher follows a cheap-to-expensive hierarchy: regulator APIs first (SEC EDGAR, Oslo Børs announcements, Companies House, Nasdaq Copenhagen), then RSS/Atom feeds, then direct HTTP GET on known IR URLs, with headless browser automation (Playwright) held in reserve only for JS-rendered or anti-bot-protected sites that defeat the first three.
The fetcher is implemented as a scheduled Python script in scripts/fetchers/, not as an agent. Filings acquisition is logistics, not intelligence, and falls under the v1 principle "Python handles logistics, Claude handles intelligence" (see 2026-05-07 "Power Automate dropped" entry). The downstream pipeline does not change — the fetcher drops PDFs into the existing filings inbox and the existing watchdog picks them up.
Reasoning: Three reasons to flag now rather than wait. (1) The architectural intent — logistics-not-agent, cheap-to-expensive hierarchy, no downstream pipeline changes — is easier to record while the reasoning is fresh than to reconstruct in v2. (2) Playwright was raised as a candidate plugin during the v1 build, and it earns no place in v1; recording where it might earn a place in v2 prevents future re-litigation of the same question. (3) Automation has real but bounded value at 6 companies — the cost-benefit shifts decisively in favour of automation when the universe expands or when MFIP transitions to unattended operation, and naming those triggers explicitly makes the v2 activation decision crisp rather than vibe-based.
Implication:

V2_BACKLOG.docx gains a fifth deferred component with the four-tier acquisition hierarchy and explicit oppstartskriterier.
No change to v1 architecture, build sequence, or tech stack.
When v2 begins: the fetcher targets the regulator-level sources first because they're the most stable, the most likely to provide structured metadata (filing type, date, fiscal year), and the least likely to break on cosmetic site redesigns.
Playwright, if eventually added, lives behind the fetcher's escalation logic. It is not a top-level dependency. requirements.txt does not pre-install it in v1.
The fetcher must populate the pdf_publication_date field that ExtractionOutput already requires (per 04_BUILD_SEQUENCE.docx Phase 4) — that field's value should come from the regulator filing metadata where available, falling back to the PDF's own front-matter date.

Affected docs: V2_BACKLOG.docx only. No changes to v1 design docs.
Revisit trigger: Three independent triggers, any of which activates v2 work on this component:

V1 stable on 6 companies for 30+ days and Magnus has bandwidth for v2.
Coverage universe expansion to 10+ companies — manual PDF acquisition becomes the bottleneck.
MFIP transitions to unattended operation (related to the v1.5 heartbeat-watchdog promotion trigger).

When activated: start with SEC EDGAR (MSFT, fully documented JSON API, lowest implementation risk) as the proof-of-concept before expanding to the European regulators.

## 2026-05-08 — Bloomberg export workflow confirmed: BDP/BDH template approach adopted

**Decision:** Bloomberg data export workflow has been redesigned from manual terminal copy-paste to a structured Excel template approach using Bloomberg's Excel Add-in (BDP/BDH formulas). Three master templates have been created and validated against live Bloomberg data at Kingston University's trading lab.

**Templates created:**
- `MFIP_Bloomberg_Export_Template_Master.xlsx` — company-specific data (8 sheets)
- `MFIP_Bloomberg_Export_Template_Indices.xlsx` — index price history (4 sheets)
- `MFIP_Bloomberg_Export_Template_FX.xlsx` — FX rate history (3 sheets)

**Workflow at lab:**
1. Open Master template, change ticker in CONFIG!B3 (one change auto-populates all BDP/BDH sheets)
2. Wait ~30 seconds for all formulas to populate
3. Paste RV_Comps manually from Bloomberg RV terminal screen (peer set is company-specific, cannot be standardised with BDP)
4. Ctrl+A → Paste Special → Values on each sheet
5. Save as `<TICKER>_<YYYY-MM-DD>.xlsx`
6. Run Indices template once per session → save as `INDICES_<YYYY-MM-DD>.xlsx`
7. Run FX template once per session → save as `FX_<YYYY-MM-DD>.xlsx`
8. All files moved to `C:\MFIP\bloomberg_inbox\`

**Confirmed working field mnemonics (tested on Kingston Bloomberg terminal):**

| Sheet | Field | Mnemonic |
|-------|-------|----------|
| BETA | Raw Beta | `BETA_RAW_OVERRIDABLE` |
| BETA | Adjusted Beta | `BETA_ADJ_OVERRIDABLE` |
| BETA | R-squared | `COEF_DETER_R_SQUARED` |
| EE | Forward EPS | `BEST_EPS` |
| EE | Long-Term Growth | `BEST_LTG_EEPS` |
| EE | Revenue Estimate | `BEST_SALES` |
| EE | EBITDA Estimate | `BEST_EBITDA` |
| EE | Consensus Rating | `BEST_ANALYST_RATING` |
| RV_Comps | EV/EBITDA | `BEST_CUR_EV_TO_EBITDA` |
| RV_Comps | P/E | `BEST_PE_RATIO` |
| RV_Comps | EV/Sales | `EV_TO_T12M_SALES` |
| RV_Comps | Price/Book | `PX_TO_BOOK_RATIO` |
| ANR | Consensus Rating | `BEST_ANALYST_RATING` |
| ANR | Buy count | `TOT_BUY_REC` |
| ANR | Hold count | `TOT_HOLD_REC` |
| ANR | Sell count | `TOT_SELL_REC` |
| ANR | Target Price | `BEST_TARGET_PRICE` |
| ANR | Coverage count | `TOT_ANALYST_REC` |
| DVD | Full history | `DVD_HIST_ALL` (BDS) |
| HP_Monthly | Monthly close | `PX_LAST` (BDH, monthly, 10Y) |
| HP_Daily | Daily close | `PX_LAST` (BDH, daily, 5Y) |

**Known data gaps — expected behaviour, not bugs:**

- `BEST_LTG_EEPS` returns `#VALUE!` for DNB and CKN — no consensus LTG available for banks and small-cap shipbrokers. DDM Agent falls back to historical DPS CAGR and sustainable growth rate from FSA Agent.
- `BEST_CUR_EV_TO_EBITDA` and `EV_TO_T12M_SALES` return `#N/A` for DNB — EV-based multiples are not meaningful for financial sector companies. P/E and P/Book are the correct multiples for banks. Comps Agent must apply sector-appropriate multiple selection.
- `BEST_CUR_EV_TO_EBITDA` and `BEST_PE_RATIO` return `#N/A` for CKN — thin analyst coverage (6 analysts). EV/Sales and P/Book populated correctly.

**BEST_ANALYST_RATING scale inversion warning:**
`BEST_ANALYST_RATING` is documented as 1=Buy, 5=Sell but returns anomalous values for some tickers (MSFT showing 4.84 despite 66 Buy / 3 Hold / 1 Sell in ANR). The raw Buy/Hold/Sell counts (`TOT_BUY_REC`, `TOT_HOLD_REC`, `TOT_SELL_REC`) are the reliable signal. `BEST_ANALYST_RATING` should be treated as indicative only — the Chief Analyst and News Agent must use raw counts as primary input.

**CKN currency note:**
CKN is UK-listed and trades in GBp (pence). Bloomberg target price (`BEST_TARGET_PRICE`) returns ~5101 USD, which reconciles correctly to ~3835 GBp at prevailing GBPUSD. The ingestion layer must be aware that CKN price fields involve a GBp → GBP → USD double conversion. Flag for Phase 3 ingestion layer build.

**RV_Comps manual paste decision:**
Peer sets are company-specific and cannot be standardised with BDP formulas (EQNR's peers are European oil majors; DNB's peers are Nordic banks; CKN's peers are shipbrokers). RV_Comps is the one sheet in the Master template that requires manual copy-paste from the Bloomberg RV terminal screen each session. All other sheets are fully automated via BDP/BDH. RV sheet should be exported in USD display currency for cross-company comparability.

**Master template fixes outstanding (to complete at home):**
- Delete duplicate `RV_Comps` BDP sheet — keep manual paste placeholder only
- Delete old `ANR` BDP sheet — rename `ANR (2)` to `ANR`

**First full export session completed 2026-05-08:**
All 8 files exported and validated:
- `EQNR_NO_2026-05-08.xlsx` ✓
- `DNB_NO_2026-05-08.xlsx` ✓
- `TEL_NO_2026-05-08.xlsx` ✓
- `NOVOB_DC_2026-05-08.xlsx` ✓
- `CKN_LN_2026-05-08.xlsx` ✓
- `MSFT_US_2026-05-08.xlsx` ✓
- `INDICES_2026-05-08.xlsx` ✓
- `FX_2026-05-08.xlsx` ✓

**Affected docs:**
- `07_BLOOMBERG_EXPORT_TEMPLATE.docx` — requires update to reflect BDP/BDH template approach, confirmed field mnemonics, RV manual paste decision, and known data gaps. Update in next doc-revision session.
- `03_TECH_STACK.docx` — no changes required (openpyxl already in stack for ingestion parsing).

**Revisit triggers:**
- If Bloomberg changes field mnemonics — re-test affected fields and update this entry.
- If CKN is replaced by a USD or EUR-listed company — CKN GBp conversion note becomes irrelevant.
- If consensus LTG becomes available for DNB or CKN — remove from known gaps list.
- Phase 3 build: implement CKN GBp double-conversion handling in ingestion layer before parsing CKN files.

## 2026-05-09 — Bloomberg storage architecture: per-company date-stamped archive, templates Git-versioned, OneDrive as lab↔home courier

**Decision:** The storage layout for Bloomberg-related files is finalised across three distinct concerns: master templates, post-export data files, and annual report PDFs. The design encodes a deliberate asymmetry between Bloomberg data (point-in-time snapshots, date-versioned) and annual report PDFs (durable artefacts, fiscal-year-versioned).

**1. Master templates — Git-versioned in the MFIP repo**

Location: `C:\MFIP\repo\templates\bloomberg\`

Three subfolders, one per template family, each containing the .xlsx template plus the initial Python parser file from Claude Code's earlier build:

- `Template_FX\` — `MFIP_Bloomberg_Export_Template_FX.xlsx`
- `Template_Index\` — `MFIP_Bloomberg_Export_Template_Indices.xlsx`
- `Template_Ticker\` — `MFIP_Bloomberg_Export_Template_Master.xlsx`

Templates are committed to Git as part of MFIP's source-of-truth alongside `decisions.md`, `requirements.txt`, agent prompt seeds, and `scripts/`. Every template change has a commit hash referenceable from `decisions.md`. Underscore-only folder names are script-safe across Python, PowerShell, and shell glob patterns.

**2. Post-export Bloomberg data — `bloomberg_archive\` with per-company date-stamped subfolders**

Location: `C:\MFIP\bloomberg_archive\`

Restructured from the original flat archive (per the 2026-05-07 "Bloomberg integration" entries) to a per-company tree with date-stamped subfolders:

```
C:\MFIP\bloomberg_archive\
├── EQNR_NO\
│   └── 2026-05-08\
│       └── EQNR_NO_2026-05-08.xlsx
├── DNB_NO\
│   └── ...
├── _INDICES\
│   └── 2026-05-08\
│       └── INDICES_2026-05-08.xlsx
└── _FX\
    └── 2026-05-08\
        └── FX_2026-05-08.xlsx
```

Underscore-prefix on `_INDICES` and `_FX` keeps shared-resource workbooks separated from the company list and sorts them to the top of the directory listing. Ticker folder names use underscores (`EQNR_NO`) matching the filename convention in `07_BLOOMBERG_EXPORT_TEMPLATE.docx` — never spaces.

The date-stamped subfolders reflect that Bloomberg exports are point-in-time snapshots: every export of EQNR captures a different state (new prices, possibly new estimates, new dividends), and all snapshots are retained for full audit trail.

**3. Annual report PDFs — `filings\` with flat per-ticker structure (no date subfolders)**

Location: `C:\MFIP\filings\<TICKER>\`

Annual reports are durable artefacts identified by fiscal year, not snapshots. Date subfolders would be noise. Once a 2024 annual report lands in `EQNR_NO\`, it's there permanently; the 2025 report joins it next year, never replaces it. PDF filename convention deferred to Phase 4 (Extractor A build) when the parser will define how it extracts fiscal year from the filename or PDF metadata.

**4. Lab↔home file transport — University OneDrive**

OneDrive (Magnus's University tenant) is the courier between the locked-down Kingston Bloomberg lab machines and the personal MFIP machine. Replaces the USB-stick option from earlier discussion. Workflow:

- Templates: edit at home → `git commit && git push` → copy to OneDrive when a lab session is approaching → open from OneDrive at the lab. Templates flow home → lab.
- Exports: lab session saves `<TICKER>_<DATE>.xlsx` files to OneDrive → home machine copies them into `bloomberg_archive\<TICKER>\<DATE>\`. Exports flow lab → home.

Templates are *not* Git-versioned at the OneDrive copy — Git remains the source of truth and OneDrive is a one-way mirror updated when templates change. If a template is ever edited at the lab in an emergency, the change must be brought back into the repo manually.

**5. `bloomberg_inbox\` reclassified as dormant in v1**

Per `04_BUILD_SEQUENCE.docx` Phase 3 and `01_ARCHITECTURE.docx`, `bloomberg_inbox\` was specified as the watchdog drop zone for ingestion-side format validation. In practice, exports flow directly from OneDrive to `bloomberg_archive\<TICKER>\<DATE>\` because Magnus is the sole file source and the export discipline enforced at the lab obviates the need for runtime format quarantine. The Phase 3 watchdog (when built) will need its scope re-evaluated — its primary use case (catching malformed automated drops) doesn't apply when a disciplined human is the only source. Decision deferred until Phase 3 starts. The inbox folder remains in place as future infrastructure.

**Reasoning:**

- Per-company date-stamped archive gives a coherent "everything for EQNR" view (`bloomberg_archive\EQNR_NO\`) without breaking the watchdog/inbox/archive separation that the Phase 3 architecture is designed around.
- Asymmetric date-handling (date subfolders for Bloomberg, no date subfolders for filings) reflects the actual temporal model of each data type — encoding "snapshot vs durable artefact" structurally rather than relying on convention.
- Templates inside `repo\` keeps everything that *defines* MFIP under a single source-of-truth. The .py files alongside each template would be orphaned from version control if templates lived outside the repo.
- OneDrive eliminates the USB-stick failure mode (forgotten stick, lost stick, stale copy) without introducing cloud dependencies into the runtime architecture — it's a courier, not a runtime component.

**Implication:**

- `01_ARCHITECTURE.docx` (Phase 3 description), `04_BUILD_SEQUENCE.docx` (Phase 3 build steps), and `07_BLOOMBERG_EXPORT_TEMPLATE.docx` (Quarantine Conditions section) all need updating in a future doc-revision session to reflect: (a) the per-company date-stamped archive structure, (b) the dormant inbox, (c) the OneDrive transport flow. Until those updates land, this entry is canonical.
- Phase 3 ingestion-layer build needs to know: skip CONFIG sheet, match RV_Comps columns by header name not position, handle CKN GBp double conversion, accept exports landing directly in `bloomberg_archive\` rather than requiring an inbox detour.
- Templates in Git means template changes get commit messages and `git diff` (binary diff is uninformative for .xlsx but the commit log itself is the audit trail). Encourage the discipline of committing template changes with descriptive messages: `templates: add target price high/low rows to ANR sheet` is more useful in three months than `update template`.

**Affected docs:** `01_ARCHITECTURE.docx`, `04_BUILD_SEQUENCE.docx`, `07_BLOOMBERG_EXPORT_TEMPLATE.docx` — all require updating in a future doc-revision session before Phase 3 build begins. This entry is canonical reference until then.

**Revisit triggers:**
- If MFIP transitions to multi-user access — OneDrive (Magnus's personal tenant) becomes a single point of failure; reconsider transport.
- If the Magnus University OneDrive account ends (graduation, account changes) — migrate to personal Microsoft account or alternative cloud transport.
- Phase 3 build start: re-scope the watchdog given exports flow directly to `bloomberg_archive\`. Possible outcomes: (a) re-purpose watchdog to validate `bloomberg_archive\` directly, (b) introduce inbox usage as part of Phase 3 to gain format-quarantine benefits, (c) drop watchdog from v1 entirely.
- If a Bloomberg-export workflow change introduces files outside Magnus's control (e.g. a teammate, an automation) — re-establish `bloomberg_inbox\` + watchdog as the canonical path.

## 2026-05-09 — Master Bloomberg template structure locked in: 7-sheet master + manual RV_Comps per company

**Decision:** The master Bloomberg export template (`MFIP_Bloomberg_Export_Template_Master.xlsx`) ships with seven sheets — six BDP/BDH/BDS data sheets plus CONFIG. RV_Comps is added per-company manually at the lab from the Bloomberg RV terminal screen, renamed from Bloomberg's default sheet name `RV` to `RV_Comps`. Saved company workbooks therefore have eight sheets total. This refines the workflow described in the 2026-05-08 "Bloomberg export workflow confirmed: BDP/BDH template approach adopted" entry — the original entry implied RV_Comps lived in the master, which would have required a placeholder sheet that gets cleared every session and reintroduces template-drift risk.

**Master template — 7 sheets:**

```
MFIP_Bloomberg_Export_Template_Master.xlsx
├── CONFIG       (input mechanism — ticker in B3, currency in B4)
├── BETA         (BDP — BETA_RAW_OVERRIDABLE, BETA_ADJ_OVERRIDABLE, COEF_DETER_R_SQUARED)
├── DVD          (BDS — DVD_HIST_ALL bulk dividend history)
├── EE           (BDP — BEST_EPS, BEST_LTG_EEPS, BEST_SALES, BEST_EBITDA, BEST_ANALYST_RATING)
├── ANR          (BQL — buy/hold/sell counts, target price, broker-level recommendation table)
├── HP_Monthly   (BDH — PX_LAST monthly, 10y)
└── HP_Daily     (BDH — PX_LAST daily, 5y)
```

All BDP/BDH/BDS/BQL formulas reference `CONFIG!$B$3` for ticker. Changing the ticker in CONFIG triggers a session-wide refresh.

**Saved company workbook — 8 sheets:**

```
<TICKER>_<YYYY-MM-DD>.xlsx
├── CONFIG       (carries through from master, retained as input documentation)
├── BETA, DVD, EE, ANR, HP_Monthly, HP_Daily   (paste-as-values from master)
└── RV_Comps     (manual paste from Bloomberg RV terminal screen, sheet renamed from RV)
```

CONFIG is intentionally retained in saved files — it documents the ticker and currency that drove the export. The Phase 3 ingestion layer skips CONFIG when parsing.

**Master template fixes already complete (2026-05-08):**

- Duplicate `RV_Comps` BDP sheet removed — RV_Comps was never a candidate for templating because peer sets are company-specific (EQNR's peers are European oil majors, DNB's are Nordic banks, CKN's are shipbrokers).
- Duplicate `ANR` sheet resolved — the BDP-based `ANR` sheet was deleted; the BQL-based `ANR (2)` was renamed to `ANR` and is the canonical analyst-recommendation sheet.

**RV column-set customisation — required at terminal:**

The default Bloomberg RV peer-screen column set is missing fields the Comps Agent requires. Before each lab session, the RV screen layout must be customised on the terminal to include — at minimum — Last Px, Mkt Cap, P/E, EV/EBITDA, P/Book, EV/Sales, ROE, Rev 1Y growth, EPS 1Y growth. The customised layout should be saved on the terminal under a memorable name (e.g. `MFIP_Default`) so it persists across sessions.

This customisation is a *human contract* — it lives on the Bloomberg Terminal, not in the MFIP repo. If the lab machine resets or the layout drifts, the next export silently has a different column set. Phase 3 ingestion mitigates this by matching columns by header name rather than position and surfacing column-set drift as an Advisory.

**Reasoning:**

- Master with 7 sheets (no RV_Comps) avoids the placeholder-sheet trap: a placeholder either gets accidentally inherited from a previous session (data integrity risk) or requires explicit clearing (extra workflow step). Adding RV_Comps fresh per company eliminates both.
- Sheet rename `RV` → `RV_Comps` aligns the manually-pasted sheet with the underscore-no-spaces convention already documented in `07_BLOOMBERG_EXPORT_TEMPLATE.docx` for the BDP/BDH/BDS sheets, and matches what Phase 3 ingestion's required-sheet list expects.
- Retaining CONFIG in saved files makes each export self-documenting — opening a file from six months ago shows immediately which ticker and currency drove it, without cross-referencing decisions.md or the filename.
- Column-set customisation deferred to terminal-side rather than encoded in the template because BQL/BDP can't override the RV screen's column selection — it's a screen-level setting, not a function-level argument.

**Implication:**

- `07_BLOOMBERG_EXPORT_TEMPLATE.docx` updates already applied in the 2026-05-09 doc-revision pass (REQUIRED SHEETS table, EXPORT SESSION CHECKLIST, and the eight-sheets-vs-seven-sheets explanation in the table caption) reflect this final state.
- Phase 3 ingestion expects 7 data sheets per company file (HP_Monthly, HP_Daily, DVD, BETA, EE, RV_Comps, ANR). The CONFIG sheet is the 8th sheet present but is metadata, not data, and is skipped during parsing.
- A test of column-set drift detection should be part of the first Phase 3 end-to-end test on EQNR data.

**Revisit triggers:**

- If Bloomberg ever offers a way to template a peer screen via BDP/BDH/BDS (currently RV is screen-bound, not function-bound) — reconsider whether RV_Comps could be templated to remove the manual-paste step.
- If the column-set customisation step proves too easy to forget — add a Pre-session checklist item to verify the RV layout name on the terminal before the first company export.
- If Phase 3 build reveals that CONFIG retention causes parser issues — reconsider whether to strip CONFIG before saving (Magnus's preference is to keep it; this would be a forced revision, not a preferred one).

## 2026-05-09 — ANR sheet enhancements deferred to next lab session

**Decision:** Three additional metrics were identified for the ANR sheet during the 2026-05-09 design review but are deferred to the next Bloomberg lab session for implementation. The metrics will improve News Agent's analyst-tracking and Chief Analyst's confidence-calibration logic, but require BQL field-name verification at a live terminal before being committed to the master template.

**Metrics to add (in priority order):**

1. **Target price high / low (consensus dispersion)**
   - **Concept:** Two new rows in the ANR top block showing the highest and lowest current target prices across the analyst panel, alongside the consensus mean already in C12.
   - **Why valuable:** Spread is signal. A consensus target of 353 NOK with a 315–430 spread carries different information than a 350–360 spread. Chief Analyst's confidence in the consensus signal should depend on dispersion. Dashboard Zone 3D (Analyst Consensus Tracker) would surface this.
   - **Implementation approach:** Pure Excel-native formulas aggregating the per-broker target column (column E) of the existing broker table — no new Bloomberg fields needed. Proposed cells:
     - `B14: Target Price High`
     - `C14: =MAX(E16:E314)`
     - `D14: Target Price Low`
     - `E14: =IFERROR(MIN(IF(E16:E314>0,E16:E314)),"-")` (array formula; ignores zeros from analysts who haven't set a target)
   - **Risk:** Lowest — no Bloomberg field-name dependency. Can be added at home without lab access. Marked priority 1 for that reason.

2. **Estimate revisions in last 4 weeks**
   - **Concept:** Two cells showing the count of upgrades and downgrades in the past month — a leading indicator that the static buy/hold/sell distribution doesn't capture.
   - **Why valuable:** If 5 analysts upgraded in the past month and 0 downgraded, that's directional momentum even when the headline distribution still shows mostly holds. News Agent's "material event flag" logic explicitly needs revision velocity.
   - **Candidate BQL/BDP fields (verify at lab):**
     - `EST_REV_UP_4WK`, `EST_REV_DN_4WK`
     - `BEST_REVISIONS_UP_4W`, `BEST_REVISIONS_DN_4W`
     - `EST_NUM_REV_UP_30D`, `EST_NUM_REV_DN_30D`
   - **Risk:** Medium — Bloomberg's revision-count field naming is inconsistent across vendor docs. Requires terminal-side verification.

3. **Rating from 4 weeks ago (rating trend)**
   - **Concept:** A second `EQY_REC_CONS` query with a 30-day-ago date offset, alongside the current rating in C11. Combined with metric 2, gives both the "what's changing" (revision counts) and "where it's heading" (rating trajectory).
   - **Why valuable:** Today's rating of 2.69 and 30-days-ago rating of 2.45 tells a different story than a flat 2.69 → 2.69. Without trajectory, Zone 3D is a snapshot rather than a trend.
   - **Implementation approach:** Re-use the existing C11 BQL pattern with a date offset. Approximate form:

     ```
     =_xll.BQL($C$6, "EQY_REC_CONS(Dates=#PriorDate)", "#PriorDate", _xll.BQL.DATE($E$6)-30)
     ```

   - **Risk:** Low-medium — structurally identical to C11 with a date shift, but BQL date-arithmetic syntax (`-30` vs `EDATE(..., -1)` vs explicit `EOMONTH`) needs lab verification.

**Reasoning:**

- Committing potentially-broken formulas to the master template now would mean every future company export silently produces `#NAME?` or `#VALUE!` errors in those cells. Better to defer than to ship broken cells.
- Metric 1 has zero Bloomberg-field risk (it's pure Excel arithmetic on data already in the sheet) and could in principle be added at home without lab access. It's bundled with metrics 2 and 3 only because changing the master template once is cleaner than three separate edits, and the next lab session is close enough to make this a reasonable trade.
- Adding fields to the master template propagates to every subsequent company export automatically — the per-company workflow doesn't change. This is the BDP/BDH approach paying off: template-level changes are universe-wide changes for free.

**Implication:**

- Next Bloomberg lab session has an explicit deliverable beyond export: verify the three field/syntax candidates above and add the working formulas to `MFIP_Bloomberg_Export_Template_Master.xlsx` ANR sheet at the lab. Commit to Git on return. The session brief for that visit should include the cell-by-cell additions worked out in advance.
- News Agent (Agent 06) and Chief Analyst (Agent 15) prompt seeds in `02_AGENT_DESCRIPTIONS.docx` may need updating once these fields exist — Chief Analyst's confidence-calibration logic should explicitly reference target price dispersion when available.
- If verification at the lab finds none of the candidate field names work — log an Advisory in `KNOWN DATA GAPS — EXPECTED BEHAVIOUR, NOT BUGS` (in `07_BLOOMBERG_EXPORT_TEMPLATE.docx`) noting the field is unavailable and the agent-side fallback. Do not block the session on a single field that doesn't resolve.

**Revisit trigger:**

- Next lab session: implement metric 1 (low risk, just do it), test candidate fields for metrics 2 and 3, commit the working version of the master template to Git, update this entry with final field names and any failed candidates.
- If Bloomberg deprecates `EQY_REC_CONS` or the revision-count fields — re-scope this entry, since the agent-side use of these fields is the primary motivation.

## 2026-05-09 — Doc-revision pass complete: Bloomberg BDP/BDH template approach documented, News Agent ANR input corrected

**Decision:** Two design documents updated in a focused doc-revision pass following the 2026-05-08 lab session at Kingston University. The design docs are now in alignment with the architectural state captured in the 2026-05-08 "Bloomberg export workflow confirmed: BDP/BDH template approach adopted" entry — decisions.md no longer supersedes the design docs on the BDP/BDH template workflow, confirmed field mnemonics, RV manual paste decision, or known data gaps.

**Docs updated this session:**

- `07_BLOOMBERG_EXPORT_TEMPLATE.docx` — four edits implementing the BDP/BDH template workflow:
  - **PURPOSE section:** rewritten to introduce the three master templates (Master, Indices, FX) replacing manual terminal exports.
  - **REQUIRED SHEETS table:** new "Bloomberg Field Mnemonic" column added between "BBG function" and "Purpose"; populated with confirmed mnemonics from the 2026-05-08 lab session (PX_LAST, DVD_HIST_ALL, BETA_RAW_OVERRIDABLE et al., BEST_EPS et al., TOT_BUY_REC et al.). RV_Comps row flagged as manual paste with USD display, sheet rename from `RV` to `RV_Comps`, and customised column set including EV/EBITDA, P/Book, EV/Sales, ROE, and growth metrics. Caption below the table updated to explain the master-vs-saved-file distinction (master ships with 7 sheets; saved company workbooks have 8).
  - **EXPORT SESSION CHECKLIST:** full rewrite from per-function manual export to template-driven workflow — pre-session add-in check, per-company workbook (open template, set CONFIG!B3, wait for formulas, paste RV manually, paste-as-values, save), Indices workbook, FX workbook, post-session checks. Session time estimate revised from ~20 min/company to ~25–35 min for the full universe.
  - **New KNOWN DATA GAPS — EXPECTED BEHAVIOUR, NOT BUGS section** inserted between QUARANTINE CONDITIONS and OUT OF SCOPE FOR V1: tabulates the BEST_LTG_EEPS gaps for DNB and CKN, the EV-multiple gaps for DNB (financial sector), the thin-coverage gaps for CKN, the BEST_ANALYST_RATING anomaly with the raw-counts mitigation, and the CKN GBp double-conversion handling.

- `02_AGENT_DESCRIPTIONS.docx` — Agent 06 News Agent Inputs: "analyst rating changes from Bloomberg EE sheet" corrected to "analyst rating changes from Bloomberg ANR sheet". Closes the deferred fix flagged in the 2026-05-09 ANR-addition decisions.md entry ("Affected docs" line for `02_AGENT_DESCRIPTIONS.docx`).

**Edits 2 and 3 evolved during the session.** The original session brief's REQUIRED SHEETS table and EXPORT SESSION CHECKLIST were drafted before two design refinements landed:

- The master template was confirmed to ship with 7 sheets (no RV_Comps placeholder), with RV_Comps added per-company at the lab from the Bloomberg RV terminal screen and renamed from `RV`. See the 2026-05-09 "Master Bloomberg template structure locked in" entry.
- The RV column-set customisation (P/E, EV/EBITDA, P/Book, EV/Sales, ROE, growth metrics) is a *terminal-side* contract — saved as a named layout on the Bloomberg Terminal, not encoded in the template — and Phase 3 ingestion will match RV columns by header name rather than position.

The applied edits reflect this final state, not the original brief's draft.

**Reasoning:** Without this alignment, the design docs and decisions.md would have continued to disagree on the Bloomberg export workflow, with decisions.md as the canonical reference and the design docs out of date. Phase 1 build (dashboard shell) needs to start from a clean, internally consistent document set; Phase 3 build (Bloomberg ingestion layer) reads `07_BLOOMBERG_EXPORT_TEMPLATE.docx` as its specification, so the doc must reflect the actual template files committed to the repo rather than the superseded manual-export workflow.

**Implication:**

- decisions.md no longer supersedes the design docs on the BDP/BDH workflow — they are now in alignment for everything settled in the original session brief.
- The CKN GBp double-conversion note in KNOWN DATA GAPS is the canonical specification for the Phase 3 ingestion-layer behaviour. The Phase 3 build must implement: (1) detect CKN ticker, (2) apply GBp → GBP unit step (divide by 100) before (3) the standard GBP → USD FX conversion via the FX workbook.
- Three areas remain where decisions.md is canonical and design docs need future updates (tracked separately, not blocking):
  - **Storage architecture** (per-company date-stamped `bloomberg_archive\<TICKER>\<DATE>\`, dormant `bloomberg_inbox\`, OneDrive transport, templates in `repo\templates\bloomberg\`) — see the 2026-05-09 "Bloomberg storage architecture" entry. Affects `01_ARCHITECTURE.docx`, `04_BUILD_SEQUENCE.docx` Phase 3, and `07_BLOOMBERG_EXPORT_TEMPLATE.docx` Quarantine Conditions.
  - **Master template structure** (7-sheet master, 8-sheet saved files, CONFIG retention) — see the 2026-05-09 "Master Bloomberg template structure locked in" entry. The relevant sections of `07_BLOOMBERG_EXPORT_TEMPLATE.docx` are already updated in this pass; no remaining gap.
  - **ANR enhancements** (target price spread, revision counts, rating trend) — see the 2026-05-09 "ANR sheet enhancements deferred" entry. Activates as a TODO at the next lab session; no immediate doc updates required until the new fields exist.

**Affected docs:** `07_BLOOMBERG_EXPORT_TEMPLATE.docx`, `02_AGENT_DESCRIPTIONS.docx` — both updated 2026-05-09.

**Revisit trigger:** None — this is a closeout entry. The architectural decisions that drove the storage layout, master template structure, and ANR enhancements carry their own revisit triggers in their respective decisions.md entries.

## 2026-05-09 — Doc-revision pass complete: storage architecture documented across design docs

**Decision:** Three design documents updated in a focused doc-revision pass to bring storage layout, lab↔home transport, and `bloomberg_inbox\` status into alignment with the storage architecture decided earlier on 2026-05-09. The design docs are now the canonical reference for these concerns; decisions.md no longer supersedes them on storage layout, transport, or dormant-inbox status. This entry closes the storage-architecture thread opened in the 2026-05-09 "Bloomberg storage architecture: per-company date-stamped archive, templates Git-versioned, OneDrive as lab↔home courier" entry, and resolves the first of three remaining-gap items flagged in the 2026-05-09 "Doc-revision pass complete: Bloomberg BDP/BDH template approach documented" closeout.

**Docs updated this session:**

- `01_ARCHITECTURE.docx` — two edits:
  - **DATA FLOW section:** PDF flow rewritten to specify that PDFs land in `C:\MFIP\filings\<TICKER>\` as durable artefacts identified by fiscal year (no date subfolder). New paragraph added describing the Bloomberg flow: lab → University OneDrive → home → `C:\MFIP\bloomberg_archive\<TICKER>\<YYYY-MM-DD>\` directly, with a note that the `bloomberg_inbox\` watcher described elsewhere in the architecture is dormant in v1 and the inbox folder remains as future infrastructure.
  - **KEY ARCHITECTURAL CONSTRAINTS list:** new bullet inserted immediately after the existing Bloomberg-scope constraint capturing the asymmetric date handling — Bloomberg as date-versioned snapshots (`bloomberg_archive\<TICKER>\<YYYY-MM-DD>\`) vs PDFs as durable artefacts (no date subfolder). Frames the asymmetry as encoding "snapshot vs durable artefact" structurally rather than by convention.

- `04_BUILD_SEQUENCE.docx` — two edits:
  - **Phase 3 Bloomberg Ingestion Layer:** v1 storage flow callout added at the top of the phase noting direct OneDrive → archive flow and dormant inbox. Four new ingestion-specific items added — skip CONFIG sheet during parsing, match RV_Comps columns by header name (not position), surface RV column-set drift as Advisory, and handle CKN GBp double conversion (divide by 100 before GBP→USD FX conversion). Quarantine-logic item reframed as documenting the contract for when the inbox is re-activated. Watchdog item replaced with a "decide watchdog scope at Phase 3 build start" item enumerating the three options on the table — (a) re-purpose watchdog to validate `bloomberg_archive\` directly, (b) introduce inbox usage as part of Phase 3 to gain format-quarantine benefits, (c) drop watchdog from v1 entirely.
  - **Phase 4 Extraction Pipeline (PDFs):** new item added flagging the PDF filename convention for `filings\<TICKER>\` as a Phase 4 build-time decision. Used by Extractor A as fallback when `pdf_publication_date` cannot be extracted from PDF metadata.

- `07_BLOOMBERG_EXPORT_TEMPLATE.docx` — two edits:
  - **QUARANTINE CONDITIONS section:** v1-status callout added immediately after the section heading, noting that the inbox flow is bypassed in v1 and validation runs only when explicitly invoked (e.g. during Phase 3 development tests). The quarantine contract itself remains documented for when the inbox is re-activated.
  - **New STORAGE LAYOUT section:** appended at the end of the doc (after RELATIONSHIP TO MODELLING AGENTS). Describes master templates at `C:\MFIP\repo\templates\bloomberg\` with three subfolders (Template_FX, Template_Index, Template_Ticker), University OneDrive as the lab↔home courier (templates flow home → lab, exports flow lab → home), post-export storage at `bloomberg_archive\<TICKER>\<DATE>\` with underscore-prefixed `_INDICES\` and `_FX\` for shared workbooks, and the separate flat `filings\<TICKER>\` structure for annual report PDFs.

**Reasoning:** The 2026-05-09 storage-architecture entry was canonical for storage layout, OneDrive transport, and the dormant inbox until these design-doc updates landed. Phase 3 build (Bloomberg ingestion layer) reads `04_BUILD_SEQUENCE.docx` and `07_BLOOMBERG_EXPORT_TEMPLATE.docx` as its specification; Phase 4 build (PDF extractors) reads `01_ARCHITECTURE.docx` data flow as its specification. Without this alignment, Phase 3 and Phase 4 build would have started from documents that disagreed with the canonical reference. With this pass complete, the design docs and decisions.md are in sync on storage concerns, and future Phase 3/4 work can read the design docs as authoritative without cross-referencing decisions.md for storage-layout questions.

**Implication:**

- decisions.md no longer supersedes the design docs on storage layout, lab↔home transport, or `bloomberg_inbox\` v1 status. The design docs are the canonical reference for these concerns going forward.
- One of the three remaining-gap items from the 2026-05-09 BDP/BDH closeout entry is now resolved. The other two — master template structure (already substantively addressed in `07` in the previous pass; closed by that entry) and ANR enhancements (deferred until next lab session) — carry their own status.
- The watchdog scope decision (a/b/c) is now formally a Phase 3 build-start deliverable, recorded in `04_BUILD_SEQUENCE.docx` Phase 3 and tracked here as the canonical place to log the eventual decision.
- The PDF filename convention is a Phase 4 build-start deliverable. When decided, log in decisions.md and update `01_ARCHITECTURE.docx` data flow to reflect the chosen pattern.

**Affected docs:** `01_ARCHITECTURE.docx`, `04_BUILD_SEQUENCE.docx`, `07_BLOOMBERG_EXPORT_TEMPLATE.docx` — all updated 2026-05-09.

**Revisit trigger:** None — this is a closeout entry. The architectural decisions that drove the storage layout carry their own revisit triggers in the 2026-05-09 "Bloomberg storage architecture" entry.

## 2026-05-09 — Pre-Phase-1 cleanup and doc-alignment pass: state validated, repo cleaned, CLAUDE.md and SYSTEM_PROMPT.docx aligned, .env created

**Decision:** Before starting Phase 1 (dashboard shell), the local MFIP state was validated against the design docs and seven gaps were closed in a single coherent pass spanning repo hygiene, doc alignment, and infrastructure. This entry records what was found, what was fixed, the resulting commits, and the off-repo changes (`.env` and the project's Custom Instructions). The pass establishes a fully validated working tree and an internally consistent doc set as the starting point for Phase 1.

**State validation outcome:**

A read-only PowerShell sweep (folder structure, Git state, venv, `.gitignore`, key files) confirmed Phase 0 deliverables intact: all eight top-level `C:\MFIP\` directories present; `bloomberg_archive\` per-company date-stamped layout matches the storage architecture (six ticker folders plus `FX\` and `INDICES\`, each with a `2026-05-08\` date subfolder); five ticker folders under `filings\` with no date subfolders (durable-artefact pattern); all 11 design docs present at `C:\MFIP\docs\`; venv healthy at `C:\MFIP\repo\.venv\`; repo on `main` synced with `origin/main` before the cleanup commits. Seven gaps surfaced; all closed in this pass.

**Gap 1 — `templates\` was untracked in Git (closed; commit `5c9db87`):**

The 2026-05-09 "Bloomberg storage architecture" entry stated that master templates are Git-versioned in `repo\templates\bloomberg\` with every change carrying a commit hash referenceable from `decisions.md`. The templates were physically present on disk but had never been `git add`ed — the canonical-source-of-truth claim was structurally true but not actually true at the commit level. Seven files added in one commit: three `.xlsx` masters (FX, Indices, Ticker) and four supporting `.py` files. Total 643 lines across the seven files.

**Gap 2 — `decisions.md` had 431 unstaged lines (closed; commit `af3f02d`):**

Two architectural entries logged earlier on 2026-05-09 were sitting in the working tree uncommitted: the ANR Consensus addition to the Bloomberg export template, and the doc-revision-pass closeout (template restructured, ANR added, Session Execution Matrix added, Build Sequence Phase 3 FX validator updated, Tech Stack feedparser row added). Both committed as a single decisions.md commit so the architectural record matched what was on the GitHub remote.

**Gap 3 — `CLAUDE.md` was stale (closed; commit `dac7e3b`):**

The Claude Code session-bootstrap file `C:\MFIP\repo\CLAUDE.md` contradicted current architecture in four places: (1) named Power Automate as the logistics layer (dropped on 2026-05-07 in favour of Python `watchdog` + Task Scheduler + `mfip_alerts.py`); (2) status block read "Pre-build... Next phase: Phase 0" when Phase 0 was complete and Phase 1 was next; (3) claimed the repo did not contain design docs (local copies exist at `C:\MFIP\docs\` per `docs\README.md`); (4) storage-layout diagram showed flat `bloomberg_archive\` with no per-company date-stamped subfolders, no shared `_INDICES\`/`_FX\`, no `repo\templates\bloomberg\`, and no `docs\` directory. File rewritten end-to-end. Substantive changes:

- **"How to start each session"** section restructured. New rule for design-doc reads: routine lookups (colour values, sheet names, zone dimensions) read local without confirmation; architectural reads (constraints, agent contracts, decisions to be encoded in code) read local then ask the user "`docs\README.md` last sync is `<date>`. Is the chat project library newer?" before proceeding. Codifies the local-as-working-copy / chat-project-as-canonical relationship from `docs\README.md`.
- **Architectural rules** expanded from 7 to 9. Rule 6 rewritten from Power Automate to "Python handles logistics, Claude agents handle intelligence" with the three-pillar specifics. New rules 8 (Bloomberg = market data only) and 9 (FSA before RE) made explicit.
- **Storage layout diagram** rewritten to match current architecture. Shows `bloomberg_inbox\` as dormant-in-v1, per-company date-stamped subfolders under `bloomberg_archive\`, underscore-prefixed `_INDICES\` and `_FX\` for shared workbooks, flat `filings\<TICKER>\` for PDFs, `models\<TICKER>\<DATE>\` for agent-generated Excel, `docs\` as local design-doc copies, `repo\templates\bloomberg\` with the three subfolders, and `.env` shown as gitignored with `python-dotenv` annotation.
- **Current status** updated from "Pre-build" to "Phase 0 complete; Phase 1 next: dashboard shell".
- **New "Ending a session" section** added at the end of the file. Sessions end only when Magnus explicitly says so. The final reply must be a handoff prompt for the next session containing: where we left off (with last commit hash if relevant); current state (clean working tree, uncommitted work, running tools); next action (single concrete step); open questions or blockers; files touched this session. Format is a single Markdown block Magnus can paste into the next session's first message. End-of-session is not inferred from the conversation tailing off.

**Gap 4 — `.env` did not exist (closed; not committed — file is gitignored by design):**

Per the 2026-05-07 logistics-layer decision, `C:\MFIP\repo\.env` should hold three values for `mfip_alerts.py` (Phase 2): `MFIP_GMAIL_APP_PASSWORD`, `MFIP_GMAIL_SENDER` (`magnus.thomass1@gmail.com`), `MFIP_GMAIL_RECIPIENT` (`magnus.t@live.no`). The file did not exist at validation time. Originally proposed to defer to Phase 2 start; Magnus elected to close it now while in scope. 2-Step Verification was already enabled; one App Password generated under the name "MFIP" via `myaccount.google.com/apppasswords`; `.env` written via PowerShell using a `Read-Host -AsSecureString` flow that prevented the password from entering shell history or appearing on screen, with the SecureString-to-plaintext conversion zeroed out of memory immediately after the file write. Verification confirmed: file exists, three lines, password length 16 characters, all three keys present, `git status --short .env` returns silence (file is ignored), `.env` appears as line 29 of `.gitignore`. Credentials remain unvalidated end-to-end until Phase 2 — `mfip_alerts.py` doesn't exist yet — but the file is in place with the right shape for `python-dotenv` to load when needed.

**Gap 5 — `SYSTEM_PROMPT.docx` was stale and in Norwegian (closed; updated in `C:\MFIP\docs\` and project library, project Custom Instructions synced):**

Three issues: (1) status block read "Pre-build" when Phase 0 was complete; (2) document list omitted `07_BLOOMBERG_EXPORT_TEMPLATE.docx` and `decisions.md` despite both being referenced throughout the project; (3) bio sentence still listed Power Automate as part of Magnus's background, which has become misleading since PA was dropped from the architecture. Magnus elected to also translate the entire document from Norwegian to English to make English the primary working language for the project (chat-side Claude continues in English; Magnus may reply in Norwegian when convenient). The full document was rewritten via the `docx` skill (unpack → edit XML → repack) to preserve all original Word styling — Arial fonts, dark blue heading colour `#1A4A7A`, table borders `#B0C8E8`, alternating cell shading `#FFFFFF` / `#F4F8FD`, blue header rule `#2E75B6`, sizes, spacing. Substantive content changes:

- **Bio sentence** trimmed: removed econometrics (irrelevant to MFIP, relevant to dissertation which is a separate project), Power Automate (dropped from architecture), Max subscription (doesn't change response shape). Kept Kingston (relevant — Bloomberg lab is part of architecture), MSc Finance (relevant — informs depth of finance discussion), Python, Bloomberg, Windows desktop.
- **Status block** updated to "Phase 0 complete. Repo, venv, GitHub remote, finance plugins, Bloomberg templates Git-versioned, .env created. Next action: Phase 1 — dashboard shell (Plotly Dash + AG Grid, four zones, placeholder data throughout). Blockers: None. Working tree clean as of the 2026-05-09 cleanup pass."
- **Document list** extended with `07_BLOOMBERG_EXPORT_TEMPLATE.docx` (Bloomberg export contract) and `decisions.md` (architectural decisions log; lives in repo, not in project library), placed in correct positions with correct alternating-shading pattern.
- **New "ENDING A SESSION" section** added at end of document, mirroring the rule added to `CLAUDE.md`. Both Claudes (chat-side architect and Claude Code builder) now share the same end-of-session protocol.

The project's Custom Instructions (the active prompt pasted into the project settings UI, distinct from the `.docx` documentation of it) was updated in parallel by Magnus to keep the active prompt aligned with the documented version. Both surfaces — the documented `.docx` and the active project instructions — are now in sync.

**Gap 6 — Superseded `.py` generator scripts under `templates\bloomberg\` (closed; commit `7b9d33c`):**

The Gap 1 commit added four `.py` files alongside the three `.xlsx` masters: `build_bbg_fx.py`, `build_bbg_indices.py`, `build_bbg_template.py`, `verify_bbg_template.py`. These were the original template-generator scripts from Claude Code's first build, written before the BDP/BDH workflow was adopted. The `.xlsx` templates have since diverged on every dimension that matters: 7-sheet master with RV_Comps added per-company at the lab, ANR added as 7th sheet on 2026-05-09, BDP/BDH formula structure, USD display-currency standardisation, FX-source decision, and the Session Execution Matrix. Running the generator scripts today would produce `.xlsx` files that do not match the canonical templates actually in use. The scripts were not Phase 3 ingestion code (Phase 3 is parsers, written in `scripts/`, written from the design-doc spec, not derived from these). Backup analysis confirmed the scripts are recoverable from Git history (`git checkout 5c9db87 -- templates/bloomberg/Template_*/`) — University OneDrive carries only `.xlsx` files lab↔home, the project library has only the `.xlsx` files, and `C:\BACKUP - MFIP\` depends on refresh timing. With Git as the canonical immutable record, deletion was the right cleanup. Four files removed in one commit (643 lines deleted); the deletion commit message itself documents the reason and recovery path so no separate `decisions.md` entry was needed at the cleanup level.

**Gap 7 — End-of-session protocol gap between Claude Code and chat-side Claude (closed alongside Gaps 3 and 5):**

The originally drafted closeout for this pass flagged the end-of-session rule as added only to `CLAUDE.md`, with the `SYSTEM_PROMPT.docx` mirror as a "possible future doc-revision item." Magnus elected to close that gap immediately rather than defer. Both surfaces now carry the same rule: a session ends only when Magnus explicitly signals it, and the final reply must be a structured handoff prompt covering where we left off, current state, next action, open questions, and files touched. End-of-session is not inferred from conversation tailing off, going quiet, or work appearing complete. Format: single Markdown block paste-ready for the next session.

**Reasoning:**

- The seven gaps shared a common root cause: each was either (a) work decided in chat but never landed in the repo, (b) doc-state lagging architectural-state, or (c) infrastructure prerequisite that would have blocked a downstream phase. Without this pass, Phase 1 would have started from a working tree where the canonical-source-of-truth claims in `decisions.md` did not match Git history, where Claude Code's session bootstrap would have misled any new session it loaded, where the chat-side Custom Instructions would have continued to mention dropped tools, and where the Phase 2 logistics layer would have hit a missing-credential blocker. Closing all seven together preserves the audit trail (one entry, one date) rather than scattering closeouts across multiple entries.
- Doing this validation pass before Phase 1 — rather than during — protects the build flow. Phase 1 is dashboard-shell work, design-and-iteration heavy, and benefits from not being interrupted by infrastructure questions about whether templates are committed, whether `.env` exists, or whether the system prompt still mentions Power Automate.
- The `.docx` editing approach (unpack → edit XML → repack, per the `docx` skill) was used after the lesson recorded earlier in 2026-05-09 — that the project library exposes `.docx` files as Markdown text extracts, and editing those extracts produces files that lose Word styling on reimport. The unpack-edit-repack approach preserved every styling element (fonts, colours, table shading, spacing). 83 text runs replaced in a single pass for the Norwegian → English translation, all matched cleanly with no fallthrough cases.
- The decision to delete the superseded `.py` generator scripts rather than mark them stale was driven by the GitHub backup story: Git history is a stronger backup than any of the four other backup mechanisms (University OneDrive, project library, `C:\BACKUP - MFIP\`, none of which actually carry the `.py` files anyway). With deletion fully reversible from `5c9db87`, the cost of "delete now and want them back later" is one Git command, while the cost of "leave clutter and step around it for months" is real friction every time the templates folder is opened.

**Implication:**

- Working tree clean as of commit `7b9d33c` plus the (gitignored) `.env` file. Phase 1 can begin from a fully validated state.
- The architectural record matches the repo state on every concern checked: storage layout, templates Git-versioning, design-doc local copies, logistics layer, session bootstrap, alerting credentials, end-of-session protocol, and template-folder hygiene.
- Both Claude surfaces (chat-side architect, Claude Code builder) share the same end-of-session rule. Handoffs between sessions — and between the two Claudes — should now produce consistently structured output.
- Project's primary working language is now English. Chat-side Claude responds in English; Magnus may reply in Norwegian when convenient. `SYSTEM_PROMPT.docx` and the active Custom Instructions are both in English.
- Gmail App Password is unvalidated until Phase 2 builds `mfip_alerts.py` and runs the first test send. If the credential proves invalid at that point — typo on paste, App Password revoked, 2SV setting changed — the recovery path is delete the entry from `myaccount.google.com/apppasswords`, generate a new one, rewrite `.env` via the same PowerShell flow.
- Storage-architecture entry's mention of "the .xlsx template plus the initial Python parser file from Claude Code's earlier build" is technically inaccurate after the Gap 6 deletion. Historical entries describe what was true at the time, not what is true now, and the deletion commit explains the change, so the historical entry was not amended.

**Affected docs (in this pass):**
- `CLAUDE.md` (in repo) — rewritten end-to-end.
- `SYSTEM_PROMPT.docx` (in `C:\MFIP\docs\` and the project library) — translated to English, structural updates, new ENDING A SESSION section.
- Project Custom Instructions (in the Claude project settings UI) — synced with the updated `SYSTEM_PROMPT.docx`.
- No design docs (the architectural design-doc set 00–07 + V2_BACKLOG) were edited; all already in alignment.

**Revisit trigger:**

- Phase 2 first SMTP test: confirm Gmail App Password works end-to-end. If it fails, follow the recovery path above and update this entry with the failure mode and resolution.
- Future Claude Code sessions: the new `CLAUDE.md` design-docs rule (read local + freshness check on architectural reads) should be confirmed working in practice. If sessions either skip the freshness check too aggressively or ask for confirmation on every routine lookup, the rule needs calibration.
- Future chat sessions: the new ENDING A SESSION rule on the chat side should be confirmed producing useful handoff prompts. If the required-fields list misses key context in practice, refine in `SYSTEM_PROMPT.docx` and `CLAUDE.md` together (both must stay in sync).
- If the project library and `C:\MFIP\docs\` drift again — i.e. one is updated and the other is not — surface it as an Advisory at the next doc-revision pass. The freshness check rule in `CLAUDE.md` is the early-warning mechanism, but is not foolproof.

## 2026-05-09 — Correction: superseded `.py` generator scripts were less divergent than the deletion entry implied

**Decision:** This entry corrects the previous "Pre-Phase-1 cleanup" entry (this same date), specifically the Gap 6 description of the four deleted `.py` template-generator scripts. On reading the actual file contents post-deletion, the divergence-from-canonical claim was overstated. The deletion is not reversed — the files remain absent from the working tree at HEAD and recoverable from Git history at `5c9db87`. This entry adjusts the record so future sessions reading `decisions.md` understand what was actually deleted.

**What the previous entry said (overstated):**

The Gap 6 description characterised the four scripts as having diverged from the canonical templates on "every dimension that matters: 7-sheet master with RV_Comps added per-company at the lab, ANR added as 7th sheet on 2026-05-09, BDP/BDH formula structure, USD display-currency standardisation, FX-source decision, and the Session Execution Matrix." It stated that "running the generator scripts today would produce `.xlsx` files that do not match the canonical templates actually in use."

**What the file contents actually showed (when read post-deletion):**

`build_bbg_template.py` (446 lines) builds a 7-sheet master workbook using the BDP/BDH formula approach. Specifically:

- **Sheet structure:** CONFIG, BETA, DVD, EE, RV_Comps, ANR, HP_Monthly, HP_Daily — matches the current canonical 7-sheet master exactly.
- **ANR sheet:** present with the correct fields — `BEST_ANALYST_RATING`, `TOT_BUY_REC`, `TOT_HOLD_REC`, `TOT_SELL_REC`, `BEST_TARGET_PRICE`, `TOT_ANALYST_REC`. The previous entry's claim that the scripts predated ANR was wrong.
- **BDP/BDH formulas:** the script uses BDP and BDH throughout (not legacy paste-from-screen). The previous entry's implication that the scripts predated the BDP/BDH workflow was wrong.
- **CONFIG-driven references:** every formula references `CONFIG!$B$3` (ticker) and `CONFIG!$B$4` (currency), matching the contract the Phase 3 parser will read against.
- **Number formats, currency overrides:** `EQY_FUND_CRNCY` parameter on currency-sensitive fields, percentage formatting on LTG, multiplier formatting on RV_Comps.

`build_bbg_fx.py` and `build_bbg_indices.py` (85 lines each) build the corresponding FX and indices workbooks with BDH formulas, instructions, and the date-stamped filename convention from the storage architecture.

`verify_bbg_template.py` (27 lines) loads the saved master and prints the BDP/BDH formulas per sheet — a sanity check, not business logic.

**Where the scripts actually diverge from the current canonical state:**

The divergence is narrow, not broad:

- **RV_Comps column set:** the script encodes 4 multiples (EV/EBITDA, P/E, EV/Sales, P/Book). The actual lab workflow uses a Bloomberg-Terminal-side named layout with additional metrics (ROE, growth metrics) and renames the sheet from `RV` to `RV_Comps`. This was always a deliberate omission — the RV column set is a *terminal-side* contract, not a template-side contract, per the 2026-05-09 storage-architecture closeout. The script's RV_Comps is a placeholder that the lab workflow overrides at the terminal.
- **Hardcoded export-end date in BDH ranges:** `build_bbg_fx.py` and `build_bbg_indices.py` hardcode `"20260508"` as the export-end date in their BDH calls. These would need to be parameterised before re-use, but that is a 2-line edit, not an architectural rebuild.

Everything else — USD display-currency standardisation, CKN GBp double-conversion handling, FX snapshot selection rule — is correctly *not* in the templates because those are runtime-side concerns (the lab checklist enforces the first; the Phase 3 parser will handle the others). The previous entry conflated "not in the template script" with "out of date in the template script." It is the former.

**Reasoning:**

- The original deletion was driven by the assumption that the scripts were architecturally stale and would produce non-current `.xlsx` files. That assumption was wrong: run today, `build_bbg_template.py` would produce a master that matches the canonical 7-sheet structure on every dimension except the deliberate RV_Comps placeholder. The scripts have genuine archival value as executable documentation of what the current `.xlsx` files contain — readable in a way that openpyxl post-hoc inspection isn't, and useful as a reference when writing the inverse Phase 3 parser.
- The deletion is nonetheless not reversed. Three reasons: (1) the files are durably recoverable from Git history at commit `5c9db87` via `git checkout 5c9db87 -- templates/bloomberg/Template_*/`, so their absence from HEAD is not data loss; (2) the canonical `.xlsx` masters themselves remain Git-versioned and serve as the authoritative artefact, so the `.py` files are reference material rather than source-of-truth; (3) flipping the deletion in a separate restore commit would clutter the history without changing the underlying availability. The cost of "leave them in history, document accurately" is lower than the cost of "restore and re-explain why they're back."
- The mistake worth flagging for future sessions: the original assessment characterised file content from filename and decisions.md context alone, without reading the actual code. When evaluating whether something is stale, read the thing. Magnus's local copies surfaced the actual content and made the correction possible.

**Implication:**

- Future sessions reading the cleanup-pass entry should also read this correction. The deletion stands; the rationale shifts from "broadly superseded" to "narrow placeholder divergence + archival reference replaced by Git history."
- If a Phase 3 parser-build session ever wants to consult the original BDP/BDH formula set as a reference for parsing, the recovery path is `git checkout 5c9db87 -- templates/bloomberg/Template_*/` into a temp location, read, then revert. The scripts are reference material, not active code.
- The same pattern of "evaluate from filename and context, then realise the content is different" should be guarded against in future doc-revision passes. When the cost of reading the file is small (it always is, for a few-hundred-line script), reading first is the right default.

**Affected docs:** None — this is a correction to the same-date cleanup-pass entry above, not a design-doc change.

**Revisit trigger:** None — this is a closeout correction. If the four `.py` files are ever restored to the working tree, log a new entry recording the restoration and its motivation.
## 2026-05-10 — Backup infrastructure: restic + Backblaze B2, automated scripts, recovery rehearsed

**Decision:** MFIP backup infrastructure is complete and verified. Restic 0.18.1 backs up C:\MFIP\ to Backblaze B2 bucket mfip-backup-magnus daily at 02:00 via Windows Task Scheduler. Monthly prune runs on the 1st at 04:00.

**Threat model:** Three failure scenarios addressed — (1) accidental deletion or file corruption (restic snapshots with 30-day daily retention), (2) hardware failure (off-site B2 storage, EU-Central region), (3) credential loss (restic password stored in iCloud Keychain as doomsday recovery).

**Storage tiers:**
- Tier 1: Git/GitHub — code and decisions log (already in place)
- Tier 2: Restic/B2 — full C:\MFIP\ backup excluding .venv\, __pycache__\, *.pyc, *.tmp, ~\$*.xlsx, .git\, OS artefacts

**Infrastructure:**
- B2 bucket: mfip-backup-magnus, Object Lock (Governance), Encryption, Private, s3.eu-central-003.backblazeb2.com
- Restic repository ID: d9d7e980
- .resticignore at epo\.resticignore — excludes .venv\ (687 MB, reproducible from requirements.txt) and build artefacts
- scripts\backup\Invoke-MfipBackup.ps1 — loads .env, runs restic backup, logs summary only to untime\backup-logs\YYYY-MM-DD.log
- scripts\backup\Invoke-MfipPrune.ps1 — monthly forget/prune (keep-daily 30, keep-weekly 12, keep-monthly 12), restic check, 90-day log retention
- scripts\backup\Task-MfipBackup.xml and Task-MfipPrune.xml — Task Scheduler entries, "Do not store password" / Interactive only mode

**Task Scheduler credential decision:** Work laptop is AzureAD-joined (employer-managed). "Do not store password" / Interactive only mode used throughout. Restic authenticates to B2 via env vars loaded from .env by the PowerShell script — no Windows network credentials needed. Tasks run when Magnus is logged in; on a sleeping laptop, runs on next wake. Acceptable for personal backup.

**Retention policy:** keep-daily 30, keep-weekly 12, keep-monthly 12. Monthly prune enforces policy and runs estic check for integrity verification.

**Recovery rehearsal (2026-05-10):**
- Restored test snapshot 7427649b (original single-file test snapshot from 2026-05-09) to C:\Temp\restic-rehearsal\
- SHA256 hash of restored decisions.md: E3853A99EAB3C5A18B0199F99B8CA2E78D9EF0FCA2514A1385911E53177114D4
- SHA256 hash of live decisions.md: E3853A99EAB3C5A18B0199F99B8CA2E78D9EF0FCA2514A1385911E53177114D4
- Result: MATCH — byte-identical restore confirmed
- Rehearsal directory cleaned up after verification

**Credential storage:**
- MFIP_B2_KEY_ID, MFIP_B2_APP_KEY, MFIP_B2_BUCKET, MFIP_B2_ENDPOINT, MFIP_RESTIC_PASSWORD stored in .env (gitignored)
- MFIP_RESTIC_PASSWORD additionally stored in iCloud Keychain as doomsday recovery — the only .env key that cannot be regenerated if .env is lost
- .env is inside C:\MFIP\repo\ and therefore caught by restic backup automatically. Anyone with restic repo access + restic password recovers all credentials. Acceptable: the password is the gate.

**Snapshots as of 2026-05-10:** 3 snapshots in repository (7427649b test, 1c8c170 first full backup, 79d5e327 second full backup post-script-fix).

**Implication:**
- Backup runs automatically. Magnus should verify untime\backup-logs\ weekly for the first month to confirm Task Scheduler is firing correctly.
- Prune script not yet tested end-to-end (would have deleted the test snapshot needed for rehearsal). Run Invoke-MfipPrune.ps1 manually once after the next scheduled daily backup completes.
- untime\unsent_alerts\ created as part of this pass — used by Phase 2 mfip_alerts.py, not yet active.

**Affected files:** scripts\backup\ (4 new files), .resticignore, untime\ directories (off-repo). Committed as 1b0926.

**Revisit triggers:**
- If employer AzureAD password rotation causes Task Scheduler tasks to stop running — re-register tasks (XML files are in repo). Check untime\backup-logs\ for gap in dates as early warning.
- If B2 costs become significant (currently negligible at ~1.5 MB stored) — review retention policy.
- Run full rehearsal (restore a complete multi-file snapshot, not just the single-file test) after the prune script has run once and confirmed clean.

## 2026-05-10 — Design pass: ideas.md introduced, V2_BACKLOG.docx retired, Agents 20 and 21 added to v1 spec

**Decision:** A design pass was completed adding two new v1 agents, retiring V2_BACKLOG.docx in favour of ideas.md, and updating all affected design docs.

**ideas.md introduced:**
ideas.md is now the canonical log for all ideas, deferred features, and backlog items. It lives in the repo alongside decisions.md and is Git-versioned. V2_BACKLOG.docx is retired — all five entries migrated to ideas.md with original rationale and start criteria preserved. Idea lifecycle: ideas.md (PROPOSED) → ideas.md (APPROVED/BACKLOG) → decisions.md (when built).

**V2_BACKLOG.docx retired:**
All five original entries (Learning Agent, Time Machine Controller, Outcome Tracker, Calibration Log, Automated Filings Acquisition) migrated to ideas.md as BACKLOG entries. Two new backlog entries added: Portfolio Manager v2 Enhancement (Kelly sizing, conflict detection, proactive rebalancing) and Sector Specialist Agent. V2_BACKLOG.docx deleted from C:\MFIP\docs\ and removed from project knowledge base.

**Agent 20 — Earnings Quality Agent (Layer 4, v1):**
Forensic earnings quality analysis: Beneish M-Score (8-variable, threshold > -1.78), Sloan accruals decomposition (1996 methodology), cash conversion trend (OCF/NI 5-year), sector-specific flags (Clarkson %-completion, Novo R&D cap, DNB provisions). Rating: CLEAN / WATCH / CONCERN / RED FLAG. RED FLAG floors Chief Analyst confidence at MEDIUM regardless of valuation convergence — non-negotiable constraint.
Trigger sequence: FSA Agent completes → Earnings Quality runs in parallel with DCF, RE Valuation, DDM, Comps → Shock Agent waits for all five. FSA reformulated statements are a hard prerequisite; falls back to raw financials with reduced confidence flag if unavailable.

**Agent 21 — Thesis Monitor Agent (Layer 5.5, v1):**
Schedule-driven daily agent — the only agent in MFIP not triggered by a new filing. Parses Chief Analyst thesis and extracts testable conditions (price, macro, growth, competitive assumptions). Four states: INTACT / WATCH / UNDER PRESSURE / BROKEN. Transitions are one-directional; never transitions downward without a new Chief Analyst recommendation. Alerts on every upward transition, never on INTACT. Requires own Task Scheduler XML entry — cannot piggy-back on backup or other scheduled tasks.
Layer 5.5 rationale: inserting cleanly between Layer 5 and Layer 6 without renumbering. Non-integer layer number is permanent and intentional.

**Doc updates (all updated 2026-05-10):**
- ideas.md — created, committed as part of b1b0926
- 02_AGENT_DESCRIPTIONS.docx — agent index updated (Layer 4 +Agent 20, new Layer 5.5 row), full spec blocks for Agents 20 and 21 added
- 01_ARCHITECTURE.docx — Layer 4 description updated to seven agents with corrected trigger sequence; Layer 5.5 row added to layer summary table
- 04_BUILD_SEQUENCE.docx — Phase 6 updated to seven agents, Earnings Quality build step added, Thesis Monitor build step added at end of Phase 7, V2 section references ideas.md
- SYSTEM_PROMPT.docx — document overview table: V2_BACKLOG.docx replaced with ideas.md; V3 clarification note updated
- CLAUDE.md — no changes needed (already clean from 2026-05-09 rewrite)
- V2_BACKLOG.docx — deleted

**Agent count after this pass:** 21 agents in v1 (was 19).

**Implication:**
- ideas.md is now the single backlog reference. V2_BACKLOG.docx references in any old notes are stale.
- Agents 20 and 21 graduate from ideas.md APPROVED to decisions.md. Their ideas.md entries should be updated to GRADUATED status.
- Phase 6 and Phase 7 build estimates increase modestly: Earnings Quality adds ~2h to Phase 6; Thesis Monitor adds ~2-3h to Phase 7.
- Thesis Monitor requires a dedicated Task Scheduler XML entry when built — pattern is identical to backup/prune tasks in scripts\backup\.

**Revisit trigger:** None — this is a closeout entry. Individual agent build decisions carry their own entries when phases are built.

## 2026-05-10 — Pre-Phase-3 Bloomberg saved-file validator

**Decision:** A one-shot Python validator (`scripts/ingestion/validate_bloomberg_workbook.py`) was built before Phase 3 begins. It encodes the saved-file contract from `07_BLOOMBERG_EXPORT_TEMPLATE.docx` (8 sheets: CONFIG + 7 data) and the v1 universe membership, validates a workbook against the contract, and emits a structured report with three result tiers (PASS / ADVISORY / FAIL) aligned with the Security Council alert system. Exit code is non-zero only on FAIL.

**Reasoning:** Phase 3 ingestion is the first build phase that consumes Bloomberg exports as production input rather than reference. Without a contract validator, contract drift (sheet renames, paste-as-values failures, RV column-set drift, currency mismatches) would surface as silent parsing bugs deep in the ingestion layer. Building the validator first means Phase 3 starts from a verified-clean input dataset, and the validator itself becomes a reusable component (the eventual watchdog handler can call `validate_workbook(path)` directly to make the quarantine decision).

**Three contract corrections were surfaced by smoke-testing the validator against the real EQNR_NO_2026-05-08 workbook:**

1. **CONFIG!B4 currency contract is fixed at "USD" for all tickers**, not the local listing currency. This matches the 2026-05-08 USD standardisation decision; the validator's first version had the local listing currency from the universe table, which was an error against the standardisation rule.

2. **RV_Comps column names are Bloomberg-native, not simplified.** The actual export uses `Mkt Cap (USD)`, `Last Px (USD)`, `Rev - 1 Yr Gr:Y`, `EPS - 1 Yr Gr:Y`, `Px/Book` (not `Mkt Cap`, `Last Px`, `Rev 1Y growth`, `EPS 1Y growth`, `P/Book` as listed in the 2026-05-09 master-template-structure entry). The validator now uses the actual Bloomberg-native names; the 2026-05-09 entry's column-set list should be read as illustrative of *which fields* are required, not as the canonical naming.

3. **Three planned columns are deliberately absent from the 2026-05-08 export and scheduled for the next lab session: `EV/EBITDA`, `Px/Book`, `EV/Sales`.** The validator handles this with a two-tier required-columns set: `RV_BASELINE_COLUMNS` (must be present, drift surfaces as `RV_COLUMN_DRIFT` Advisory) and `RV_PLANNED_COLUMNS` (informational `RV_PLANNED_COLUMN_PENDING` Advisory until they're added). When the next lab session adds them, promote the three names from `RV_PLANNED_COLUMNS` to `RV_BASELINE_COLUMNS` in the validator and the Advisory disappears automatically.

**Smoke-test result against the 2026-05-08 archive:** `PASS=0 ADVISORY=6 FAIL=0`, exit code 0. Five workbooks each carry the planned-columns Advisory; TEL_NO carries the universe-member-absent Advisory. No FAILs — saved-file contract holds end-to-end.

**Implication:**

- The validator is a Phase 3 prerequisite, not a Phase 3 deliverable. It runs ad-hoc against `bloomberg_archive\` to confirm contract conformance before any other ingestion code is written. After Phase 3 ingestion is built, the same `validate_workbook()` function will be wrapped by the watchdog handler at the inbox quarantine boundary if `bloomberg_inbox\` is ever re-activated.
- The "find latest workbook per company" logic lives in the validator's `--all` mode for now. When Phase 3 build starts, this logic should be lifted out into a shared helper (target: `scripts/ingestion/archive_lookup.py`) — the watchdog watcher will need it too.
- TEL_NO is in the validator's `KNOWN_ABSENT` set (universe member, not yet exported at the lab). When the next lab session adds TEL_NO data, remove it from `KNOWN_ABSENT`.
- A folder-vs-doc mismatch surfaced during this work: `bloomberg_archive\` on disk uses `INDICES\` and `FX\` (no leading underscore) but `CLAUDE.md` documented `_INDICES\` and `_FX\`. Resolution: update docs to match disk. `CLAUDE.md` updated 2026-05-10; `01_ARCHITECTURE.docx` and `07_BLOOMBERG_EXPORT_TEMPLATE.docx` deferred to next doc-revision pass.

**Affected docs:** `CLAUDE.md` (storage-layout section, this pass). `01_ARCHITECTURE.docx`, `07_BLOOMBERG_EXPORT_TEMPLATE.docx` — deferred. `decisions.md` 2026-05-09 master-template-structure entry — RV column-set list is illustrative, not canonical; actual Bloomberg-native names are in the validator.

**Revisit triggers:**

- Next lab session: add `EV/EBITDA`, `Px/Book`, `EV/Sales` to the terminal-side RV layout. Then promote those three names from `RV_PLANNED_COLUMNS` to `RV_BASELINE_COLUMNS` in the validator and remove TEL_NO from `KNOWN_ABSENT` once exported.
- Phase 3 ingestion build start: lift the "find latest workbook" logic into a shared helper and have the watchdog handler call `validate_workbook()` directly at the quarantine boundary.
