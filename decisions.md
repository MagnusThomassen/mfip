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