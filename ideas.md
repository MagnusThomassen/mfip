# MFIP — Ideas Log

This file records ideas that have been raised, discussed, and deemed worth keeping
but not yet built. An entry here means: "this is interesting, well-formed enough to
act on later, and should not be lost or re-derived."

This file replaces V2_BACKLOG.docx, which has been retired. All five entries from
that document have been migrated here. The file lives in the repo alongside
decisions.md and follows the same Git versioning policy.

**Lifecycle of an idea:**

Most entries follow the build trajectory:

```
ideas.md (PROPOSED)
    → ideas.md (APPROVED — assigned to v1 build, pending doc update)
    → ideas.md (BACKLOG — confirmed deferred, start criterion defined)
    → decisions.md (when built and implemented)
```

A small number of entries are permanent reference anchors that exist to be
consulted rather than built. These are off-trajectory and stay marked
`REFERENCE` indefinitely.

**Status values:**
- `PROPOSED` — raised and discussed, not yet decided
- `APPROVED` — decided for v1, pending doc update and build phase assignment
- `BACKLOG` — decided as deferred; has a defined start criterion
- `GRADUATED` — built; entry archived here for reference, live record in decisions.md
- `REFERENCE` — permanent anchor entry; exists to be consulted, not built. Off the build trajectory. Reviewed periodically rather than decided on.

Format: date raised, idea, rationale, proposed design, prompt seed (if agent),
status, decision gate.

---

## 2026-05-09 — Earnings Quality Agent

**Idea:** Add a dedicated Earnings Quality Agent to Layer 4. Separate from FSA Agent,
whose mandate is reformulation and DuPont. This agent's mandate is purely forensic:
can these earnings be trusted?

**Rationale:** Earnings quality analysis is a core analytical objective for MFIP, not
a secondary check. The FSA Agent produces an accruals ratio as a byproduct — that is
insufficient. A proper earnings quality layer applies Beneish M-Score (8-variable),
Sloan accruals decomposition, cash conversion trend analysis, and sector-specific
revenue recognition flags. For the coverage universe: Clarkson (percentage-of-
completion revenue), Novo Nordisk (R&D capitalisation), DNB (loan loss provisioning).
Output is a rating (CLEAN / WATCH / CONCERN / RED FLAG) that explicitly calibrates
Chief Analyst confidence — a RED FLAG floors Chief Analyst confidence at MEDIUM
regardless of valuation method convergence.

**Proposed design:**
- Position: Layer 4. Waits for FSA Agent output (reformulated statements are a hard
  prerequisite), then runs in parallel with DCF / RE Valuation / DDM / Comps agents.
  Shock Agent waits for its output alongside the others.
- Inputs: Enriched Investment Package (from Context Synthesiser), FSA Agent
  reformulated statements, Extractor B narrative flags (accounting policy changes,
  auditor concerns).
- Outputs:
  - EarningsQuality JSON: Beneish M-Score (8-variable), Sloan accruals decomposition
    (working capital / non-cash / financing components), cash conversion quality score
    (OCF / Net Income across 5 years), revenue recognition risk flags, 5-year trend
    for every metric.
  - Earnings Quality Rating: CLEAN / WATCH / CONCERN / RED FLAG.
  - Narrative explanation of every flag raised, including exact metric, threshold
    breached, and year it first appeared.
- Key behaviour:
  - Beneish M-Score > -1.78 triggers RED FLAG (manipulation probability threshold).
  - Sloan decomposition follows the 1996 methodology.
  - Cash conversion: OCF/NI persistently <0.8 for 3+ consecutive years = CONCERN.
  - Cross-references Extractor B accounting policy change flags — any policy change
    in a year with improving earnings trend is automatically WATCH.
  - 5-year trend produced for all metrics, never point-in-time only.
  - Sector-specific flags: Clarkson (% completion), Novo (R&D cap), DNB (provisions).
- Failure mode: if FSA reformulated statements unavailable, runs on raw financials
  with reduced confidence flag. Never blocks the pipeline.
- Feeds into: Chief Analyst as trust-calibration input. RED FLAG floors Chief Analyst
  confidence at MEDIUM regardless of valuation convergence.

**Prompt seed:**
You are the Earnings Quality Agent for MFIP. Your sole mandate is forensic: can
these earnings be trusted? You apply Beneish M-Score, Sloan accruals decomposition,
and cash conversion analysis across five years. You work from the FSA Agent's
reformulated statements — not raw filings — because reformulation has already
separated operating from financing activities. Your output is a rating (CLEAN /
WATCH / CONCERN / RED FLAG) with a narrative that a portfolio manager can read in
90 seconds. You flag sector-specific risk patterns: percentage-of-completion revenue,
R&D capitalisation, loan loss provisioning. Every flag includes the exact metric, the
threshold breached, and the year it first appeared. You never modify financial data
and you never make a buy/sell recommendation — your job is to tell the Chief Analyst
how much to trust the numbers before valuation conclusions are drawn.

**Status:** `GRADUATED` — doc update complete 2026-05-10. Full spec in
02_AGENT_DESCRIPTIONS.docx (Agent 20). Layer 4 updated in 01_ARCHITECTURE.docx.
Build step added to 04_BUILD_SEQUENCE.docx Phase 6. Live record in decisions.md
entry 2026-05-10.

**Decision gate:** N/A — graduated.

---

## 2026-05-09 — Thesis Monitor Agent

**Idea:** Add a Thesis Monitor Agent at Layer 5.5 — after Portfolio Manager — whose
sole job is to watch whether the conditions underpinning each live investment thesis
are still intact, and alert Magnus when they are not.

**Rationale:** Without this agent, MFIP is a point-in-time analysis engine. The
Thesis Monitor is what makes it a monitoring system. Chief Analyst extracts testable
conditions from each thesis (price assumptions, macro assumptions, growth assumptions,
competitive assumptions) and the Thesis Monitor evaluates them continuously. It is
the only agent in MFIP that runs on a schedule rather than being triggered by a new
filing — architecturally distinct and important to preserve that distinction.

**Proposed design:**
- Position: Layer 5.5. Runs continuously on a daily schedule during market hours.
  Not triggered by new filings — the only schedule-driven agent in the system.
- Inputs: Active positions and thesis conditions from Portfolio Manager, latest
  MacroContext JSON (from Macro Agent ongoing feed), latest NewsEvents JSON (from
  News Agent ongoing feed), HP_Daily price data (most recent Bloomberg export).
- Outputs:
  - ThesisStatus JSON per active position: INTACT / WATCH / UNDER PRESSURE / BROKEN.
  - Per-company thesis condition checklist with current status of each condition.
  - Alert payload for dashboard and Gmail on every upward status transition. Never
    alerts on INTACT.
- Key behaviour:
  - At initialisation, parses Chief Analyst thesis and extracts explicit testable
    conditions (e.g. "thesis assumes EQNR Brent >$70", "thesis assumes DNB NIM
    expansion continuing", "thesis assumes MSFT Azure growth >20% YoY").
  - Status transitions: INTACT → WATCH (one condition deteriorating) → UNDER
    PRESSURE (two or more conditions deteriorating) → BROKEN (core condition
    definitively failed).
  - Transitions are one-directional — never transitions downward without a deliberate
    re-analysis by Chief Analyst issuing a new recommendation.
  - Alerts on every upward transition. Never alerts on INTACT.
  - Never recommends action — surfaces conditions, Magnus decides.
  - If price data is stale (>5 trading days), flags data gap and continues monitoring
    narrative conditions only.
- Failure mode: stale price data does not silence the agent — monitoring continues
  on narrative conditions with a clearly flagged data gap.
- Feeds into: Dashboard (thesis status panel, one row per active position), Gmail
  alerts (WATCH or worse), Portfolio Manager (thesis status enriches position
  tracking).

**Prompt seed:**
You are the Thesis Monitor Agent for MFIP. Your job is to watch the conditions that
make each investment thesis valid, and tell Magnus the moment those conditions start
to break down. When Chief Analyst issues a recommendation, you parse the thesis and
extract every testable condition — price assumptions, macro assumptions, growth
assumptions, competitive assumptions. On every monitoring cycle you check each
condition against current data. You have four states: INTACT, WATCH, UNDER PRESSURE,
BROKEN. You transition upward when conditions deteriorate; you never transition
downward without a deliberate re-analysis by Chief Analyst. You alert on every upward
transition. You never alert on INTACT. You never recommend buying or selling — you
surface what is changing, Magnus decides what to do about it.

**Status:** `GRADUATED` — doc update complete 2026-05-10. Full spec in
02_AGENT_DESCRIPTIONS.docx (Agent 21). Layer 5.5 added in 01_ARCHITECTURE.docx.
Build step added to 04_BUILD_SEQUENCE.docx Phase 7. Live record in decisions.md
entry 2026-05-10.

**Decision gate:** N/A — graduated.

---

## 2026-05-09 — Portfolio Manager v2 Enhancement

**Idea:** Expand the Portfolio Manager's mandate in v2 to include position sizing
logic, cross-portfolio conflict detection, and proactive rebalancing triggers. The
v1 Portfolio Manager routes recommendations and tracks positions. It does not reason
about how much to allocate and has no mechanism to detect conflicting theses across
strategies.

**Rationale:** The v2 enhancement converts the Portfolio Manager from a passive
tracker to an active portfolio construction tool. Kelly criterion sizing makes
allocation decisions principled rather than arbitrary. Cross-portfolio conflict
detection prevents the system from simultaneously holding contradictory views on the
same company across strategies. Proactive rebalancing triggers close the loop between
Thesis Monitor Agent signals and portfolio action proposals.

**Proposed design:**
- Position sizing: Kelly criterion adjusted by Chief Analyst confidence level.
  HIGH confidence = full Kelly, MEDIUM = half Kelly, LOW = quarter Kelly.
  Hard cap: no single position exceeds 20% of any strategy.
- Cross-portfolio conflict detection: the same company cannot hold a BUY thesis in
  one strategy and a SELL thesis in another without an explicit Magnus override.
  Conflict surfaced as a WARNING on dashboard and via Gmail alert.
- Proactive rebalancing triggers — proposals generated automatically when:
  - A position drifts >5% from target weight.
  - Thesis Monitor Agent signals UNDER PRESSURE or BROKEN for a held position.
  - Portfolio-level Sharpe ratio drops below the strategy's defined floor.
- Every rebalancing proposal includes the before/after portfolio state so Magnus
  can evaluate the change at a glance. No autonomous execution — propose only.

**Prompt seed (v2):**
You are the Portfolio Manager for MFIP v2. You manage four portfolio strategies with
distinct mandates. You are responsible for position sizing, not just position
selection. For each recommendation routed to a strategy, you compute an allocation
using Kelly criterion adjusted for Chief Analyst confidence (HIGH = full Kelly,
MEDIUM = half Kelly, LOW = quarter Kelly). You enforce hard concentration limits: no
single position exceeds 20% of any strategy. You detect cross-portfolio conflicts —
the same company cannot carry a BUY thesis in one strategy and a SELL thesis in
another without an explicit Magnus override. You generate rebalancing proposals
proactively when a position drifts >5% from target weight, when Thesis Monitor
signals UNDER PRESSURE or BROKEN, or when portfolio-level Sharpe drops below the
strategy's defined floor. You never execute — you propose with full reasoning,
including the before/after portfolio state so Magnus can evaluate the change at a
glance.

**Status:** `BACKLOG` — deferred to v2. Not built in v1.

**Decision gate:** v1 stable on all 6 companies for 30+ days AND Portfolio Manager
v1 routing verified correct across all four strategies. At that point evaluate
whether to promote and assign to a v2 build phase.

---

## 2026-05-09 — Sector Specialist Agent

**Idea:** Add a Sector Specialist Agent at Layer 3.5 — between Intelligence Synthesis
and Modelling — that translates sector-specific KPIs into inputs the modelling agents
actually need, rather than relying on generic context from the Context Synthesiser.

**Rationale:** The coverage universe spans five materially different sectors: energy
(EQNR), financials (DNB), telecom (TEL), healthcare (NOVO B), shipbroking (CKN).
Valuing DNB requires understanding Basel III CET1 ratios and NIM trends. Valuing
EQNR requires reserve replacement ratios and production cost per boe. Valuing CKN
requires Baltic Dry Index cycle positioning. Without sector translation, modelling
agents apply generic frameworks to sector-specific businesses. A Sector Specialist
agent would supply the sector lens that sits between macro context and the valuation
models. Relevant when the coverage universe scales beyond the current 6 companies and
sector diversity increases.

**Proposed design (outline — detail to be fleshed out at activation):**
- Position: Layer 3.5, runs after Context Synthesiser, feeds Enriched Investment
  Package with an additional SectorContext block before it reaches modelling agents.
- One agent per sector, or one agent with sector-switching logic — to be decided at
  build time based on implementation complexity.
- Sector KPI sets (indicative):
  - Energy (EQNR): reserve replacement ratio, production cost per boe, lifting cost,
    Brent breakeven, North Sea capex cycle.
  - Financials (DNB): CET1 ratio, NIM trend, loan loss provision rate, ROE vs cost
    of equity, Norwegian housing exposure.
  - Telecom (TEL): ARPU trend, churn rate, network capex cycle, spectrum renewal
    obligations.
  - Healthcare (NOVO B): pipeline newsflow, patent cliff exposure, pricing pressure
    in key markets, R&D capitalisation policy.
  - Shipbroking (CKN): Baltic Dry Index, fleet utilisation, order book as % of fleet,
    counter-cyclical positioning.
- Not built in v1: too much bespoke logic for 6 companies. Generic Context Synthesiser
  is sufficient at current scale. Hard-coded sector-specific prompt extensions in
  modelling agent system prompts are the v1 approach.

**Status:** `BACKLOG` — deferred to v2 or later.

**Decision gate:** Coverage universe expands to 10+ companies with increased sector
diversity, OR v1 usage reveals persistent sector-blind errors in modelling agent
outputs that cannot be addressed by prompt refinement alone.

---

## 2026-05-09 — Learning Agent (migrated from V2_BACKLOG.docx)

**Idea:** An agent that reads decision and outcome logs, identifies systematic biases
in agent outputs, and pushes calibration updates back to affected modelling agents.

**Rationale:** The system cannot improve itself without outcome data. The Learning
Agent is the self-improvement mechanism — but it requires a minimum dataset before
it can do meaningful work. Building it before that data exists produces an agent with
nothing to learn from. The v1 logging infrastructure (decision_log, security_log)
captures the data the Learning Agent will consume when activated.

**Proposed design:**
- Inputs: Decision Log (all recommendations), Outcome Log (actual prices at 30/60/90
  days post-recommendation — requires Outcome Tracker, see separate entry), Calibration
  Log (all previous calibration updates).
- Outputs: Calibration Update packages for affected agents, Calibration Log entries,
  Monthly Accuracy Report for dashboard.
- Key behaviour: runs weekly after first 30 days; adjustable to daily. Minimum 10
  data points before issuing any calibration update on a given assumption. Updates
  are directional nudges, not overrides. Documents evidence base for every update.
  Tracks its own calibration accuracy over time.
- Failure mode: v1 logging captures the data; agent simply does not activate until
  start criterion is met.
- Note: agent is already specified in 02_AGENT_DESCRIPTIONS.docx (Agent 17) with
  full Role, Inputs, Outputs, Key Behaviour, Failure Mode, and Prompt Seed. That
  spec is the build reference when this is activated.

**Status:** `BACKLOG` — deferred to v2. Not built in v1.

**Decision gate:** At least 30 BUY/SELL recommendations logged in decision_log with
corresponding outcome data at 30/60/90 days. Without this data, the agent has nothing
to learn from.

---

## 2026-05-09 — Time Machine Controller / Bloomberg Backtesting (migrated from V2_BACKLOG.docx)

**Idea:** A component that lets the full agent pipeline replay on historical dates,
with strict temporal isolation to prevent look-ahead bias. Validates Learning Agent
calibration accuracy against historical counterfactuals.

**Rationale:** Backtesting is a validation mechanism — it cannot validate a system
that has not yet been built. The Time Machine Controller is the mechanism for
confirming that calibration updates from the Learning Agent actually improve
predictive accuracy. It requires both a working v1 pipeline and historical Bloomberg
export data before it adds value.

**Proposed design:**
- Inputs: Historical Bloomberg exports (requires v2 batch import capability),
  simulation date, target company.
- Outputs: Temporally-isolated dataset for a given historical date, simulation result
  (full pipeline output as if run on that date), comparison against actual outcome.
- Key behaviour: strict temporal isolation — no forward-looking data ever leaks into
  a historical simulation. Full pipeline replay (all agents) on the simulation date.
  Results logged to backtest-specific log tables, separate from production logs.
- Failure mode: if temporal isolation cannot be guaranteed for a given simulation,
  refuses to run it. No partial simulations.
- Note: agent is already specified in 02_AGENT_DESCRIPTIONS.docx (Agent 18) with
  full Role, Inputs, Outputs, Key Behaviour, Failure Mode, and Prompt Seed. That
  spec is the build reference when this is activated.

**Status:** `BACKLOG` — deferred to v2. Not built in v1.

**Decision gate:** v1 has delivered its first end-to-end recommendation on at least
3 companies AND Learning Agent is active. Backtesting without a working pipeline and
calibration data to validate produces no analytical value.

---

## 2026-05-09 — Outcome Tracker (migrated from V2_BACKLOG.docx)

**Idea:** Automated evaluation of Chief Analyst recommendations at 30, 60, and 90
days post-issue — comparing the predicted price target with actual price at each
interval.

**Rationale:** Without outcome tracking, the Learning Agent has no data to learn
from. The Outcome Tracker is the data collection mechanism that makes the
self-improvement loop possible. It is a prerequisite for the Learning Agent, not a
standalone feature.

**Proposed design:**
- For each recommendation in decision_log, schedule price lookups at T+30, T+60,
  T+90 trading days.
- Compare actual price against predicted price target at each interval.
- Log result to outcome_log (separate from decision_log and security_log).
- Compute hit rate (% of BUY recommendations that were up at T+90, etc.) for
  dashboard display.
- Implemented as a scheduled Python script (logistics layer), not an agent.
  "Python handles logistics, Claude handles intelligence."

**Status:** `BACKLOG` — deferred to v2. Not built in v1. v1 builds only decision_log
and security_log. outcome_log and calibration_log are not built until v2.

**Decision gate:** Learning Agent activation. Outcome Tracker and Learning Agent are
built together as the v2 self-improvement package.

---

## 2026-05-09 — Calibration Log + Self-Improvement Loop (migrated from V2_BACKLOG.docx)

**Idea:** Structured logging of every calibration update the Learning Agent makes,
with before/after values and the evidence base that justified each change. Enables
the Learning Agent to track its own calibration accuracy over time.

**Rationale:** Without a Calibration Log, the Learning Agent's updates are
unauditable. The log ensures every assumption change is traceable to specific outcome
data, prevents the system from making poorly-evidenced adjustments, and gives Magnus
visibility into how the system is changing its own behaviour.

**Proposed design:**
- A structured log table (calibration_log) separate from decision_log, outcome_log,
  and security_log.
- Each entry: timestamp, affected agent, assumption changed, old value, new value,
  evidence base (references to specific outcome_log entries), confidence in the
  update.
- Learning Agent writes to calibration_log; no other agent or Python script modifies
  it.
- Dashboard: monthly calibration summary panel (what changed, why, what the effect
  was).

**Status:** `BACKLOG` — deferred to v2. Not built in v1. Requires Learning Agent.

**Decision gate:** Learning Agent activation. Calibration Log is part of the same
v2 self-improvement package as Outcome Tracker and Learning Agent.

---

## 2026-05-09 — Automated Filings Acquisition (migrated from V2_BACKLOG.docx)

**Idea:** A scheduled Python fetcher that monitors regulatory feeds and company IR
pages for new annual and preliminary reports, and drops PDFs to
`C:\MFIP\filings\<TICKER>\` where the existing watchdog picks them up. v1 uses
manual PDF drop — this automates that step.

**Rationale:** For 6 companies where Magnus visits IR pages quarterly as part of
his own analysis, automation adds marginal value. The value becomes significant when
the coverage universe expands or when MFIP moves to unattended operation. Building
this in v1 would be premature optimisation.

**Proposed design:**
- Implemented as a scheduled Python script in `scripts/fetchers/` — not an agent.
  Filings acquisition is logistics, not intelligence. Follows the v1 principle
  "Python handles logistics, Claude handles intelligence."
- Four-tier acquisition hierarchy (cheapest to most expensive):
  1. Regulator APIs: SEC EDGAR (MSFT), Oslo Børs announcements (EQNR/DNB/TEL),
     Companies House (CKN), Nasdaq Copenhagen (NOVO B).
  2. RSS/Atom feeds from IR pages where available.
  3. HTTP GET on known IR URLs with stable file paths.
  4. Headless browser (Playwright) as last resort for JS-rendered or anti-bot-
     protected sites. Playwright is not installed in v1 — held in reserve.
- Fetcher populates the pdf_publication_date field that ExtractionOutput already
  requires (per 04_BUILD_SEQUENCE.docx Phase 4). Source: regulator filing metadata
  where available, falling back to PDF front-matter date.
- Downstream pipeline unchanged — fetcher drops files into existing filings inbox,
  existing watchdog picks them up.
- Start with SEC EDGAR (MSFT) as proof-of-concept — fully documented JSON API,
  lowest implementation risk — before expanding to European regulators.

**Status:** `BACKLOG` — deferred to v2. Not built in v1.

**Decision gate:** Any one of the following three triggers:
  1. v1 stable on 6 companies for 30+ days AND Magnus has bandwidth for v2 work.
  2. Coverage universe expands to 10+ companies — manual PDF acquisition becomes
     the bottleneck.
  3. MFIP transitions to unattended operation (related to the v1.5 heartbeat-watchdog
     promotion trigger).

---

## 2026-05-10 — agentic-stack (Cross-Agent Memory Layer)

**Idea:** A portable `.agent/` folder — memory, skills, and protocols — that
drops into any project and bridges context across coding agents (Claude Code,
Cursor, Codex, etc.) so nothing resets when switching tools.

**Reference:** https://docs.google.com/document/d/1METHh0SeUsMPbz3Ct69_bT-kiby0W1qPbH6Dzy_V9QU/mobilebasic
**Repo:** github.com/codejunkie99/agentic-stack

**Rationale:** Not relevant to the current build — context persistence is
handled by this Claude Project and its knowledge base. Becomes relevant if
Magnus moves to Claude Code as the primary coding harness for later build
phases. Windows PowerShell installer exists (install.ps1).

**Status:** `PROPOSED` — noted for reference. No decision needed until Claude
Code is adopted as primary harness.

**Decision gate:** Magnus switches to Claude Code for active development.

---

## 2026-05-10 — Claude Dreams (Managed Agent Memory Consolidation)

**Idea:** Use Anthropic's Dreams API to automatically consolidate agent memory
stores across sessions — merging duplicates, resolving contradictions, removing
stale entries, and converting all relative dates to absolute ISO-8601 dates.

**Reference:** https://docs.google.com/document/d/1XTkK-egpBIRYkSQz7IH9Y60tX1U8iFv5EUqYG7RkBxg/mobilebasic
**Docs:** platform.claude.com/docs/en/managed-agents/dreams
**Status at time of logging:** Research preview (announced May 6, 2026).

**Rationale:** The memory degradation problem Dreams solves is real for MFIP.
Thesis Monitor accumulates superseded thesis conditions across monitoring cycles.
Learning Agent accumulates calibration context across many recommendations. Without
consolidation, both agents will produce inconsistent outputs over time. The Dreams
pattern — never modify the input store, always produce a new output store for
review — is also the right model for MFIP's own memory hygiene regardless of
whether the API itself is adopted.

**Dependency:** MFIP v1 agents are Claude API calls orchestrated by Python with
state in local SQLite/JSON — not Anthropic managed memory stores. Adopting Dreams
requires migrating agent state management to Anthropic's hosted memory layer.
That is a meaningful architectural decision, not a drop-in addition.

**Status:** `PROPOSED` — noted for reference. No decision until v2.

**Decision gate:** Learning Agent and Thesis Monitor are both active AND Dreams
has reached GA (out of research preview). Evaluate then whether to migrate agent
state to managed memory stores or implement equivalent consolidation logic locally.

## IDEA-012 — Web-first frontend migration (post-Mac Mini)

**Status:** PROPOSED
**Added:** 2026-05-11
**Source:** Dashboard knowledge base README (brainstorm session 2026-05-11)

**The idea:**
Migrate the MFIP frontend from Plotly Dash (Python, desktop) to a
web-first stack: TypeScript + React + Next.js + Vercel. Accompanied
by a component library shift to Tremor + Recharts + shadcn/ui and
state management via Zustand.

**What triggers the idea:**
The dashboard knowledge base README (separate from MFIP core docs)
was written with a web-first architecture in mind. The JSX prototype
built 2026-05-11 already uses React patterns and demonstrates that
the visual target is achievable in that stack. Mac Mini M4 (autumn
2026) and Claude Code adoption are natural migration enablers.

**The case for:**
- Tremor + shadcn/ui produce significantly better-looking financial
  dashboards than Plotly Dash with less custom CSS effort
- Next.js enables future remote access (view portfolio from phone,
  share a read-only view with Helene, etc.)
- TypeScript catches data shape errors at compile time — valuable
  when wiring Bloomberg exports to chart components
- Claude Code workflows are better documented for TypeScript/React
  than for Python/Dash
- The JSX prototype is already 80% of the visual work — migration
  cost may be lower than it appears

**The case against:**
- MFIP's automation layer (watchdog, DuckDB, ingestion scripts,
  Task Scheduler) is pure Python and stays Python regardless — the
  migration only affects the presentation layer, not the data layer
- Plotly Dash may be entirely sufficient for a single-user desktop
  tool — the complexity of Next.js may not be justified
- Vercel hosting introduces a cloud dependency that the current
  architecture deliberately avoids
- A frontend migration mid-project creates context-switching cost
  and risks stalling the agent pipeline work, which is the core
  of MFIP's value

**What needs to be true before APPROVAL:**
1. MFIP v1 is complete — all agents built, pipeline running,
   Dash dashboard functional with real data
2. Mac Mini acquired and Claude Code set up
3. Honest evaluation: does Dash v1 feel limiting in practice,
   or is it good enough?
4. Migration cost scoped — estimate sessions required to rebuild
   the dashboard layer in Next.js without touching the Python stack

**If approved, affects:**
- `03_TECH_STACK.docx` — frontend section rewrite
- `05_DASHBOARD_SPEC.docx` — component library references
- `01_ARCHITECTURE.docx` — presentation layer description
- New doc: `08_FRONTEND_MIGRATION.docx`

**Revisit date:** After Mac Mini acquisition — no earlier.

## IDEA-013 — Waterfall chart on Company Financials tab

**Status:** PROPOSED
**Added:** 2026-05-11
**Source:** Dashboard reference docs review (session 2026-05-11)

**The idea:**
Add a P&L waterfall chart to the Company deep-dive Financials tab.
Walk from Revenue → Gross Profit → EBIT → Net Income. Selectable
between single-year and 5-year comparison view. Data source: FSA
Agent output (already computed from annual report PDFs).

**Why it fits:**
MFIP already runs FSA and DuPont reformulation — the numbers exist.
A waterfall is the most intuitive visual for showing where margin
is made or lost across the P&L structure. Currently missing from
the prototype entirely.

**Build note:**
Plotly has a native waterfall chart type — no D3 required in Dash v1.
In a future web-first stack, D3 or react-financial-charts is the
right tool.

**Start criteria:**
FSA Agent is built and producing reformulated P&L output (Phase 6).

---

## IDEA-014 — RAG company status grid on Master dashboard

**Status:** PROPOSED
**Added:** 2026-05-11
**Source:** Dashboard reference docs review (session 2026-05-11)

**The idea:**
Replace the current single MFIP metrics block on the Master dashboard
with a 2×3 RAG tile grid — one tile per company in the universe.
Each tile shows: ticker, company name, Thesis Monitor state
(INTACT / WATCH / UNDER PRESSURE / BROKEN) as the RAG colour,
and last-updated timestamp.

**Why it fits:**
The Thesis Monitor agent (Agent 21, Layer 5.5) already produces
exactly these four states. Green / Amber / Amber / Red maps
directly. The Master dashboard becomes a genuine one-glance
portfolio health check rather than a static project card.

**Start criteria:**
Thesis Monitor Agent (Agent 21) is built and running (Phase 7).
Dashboard shell (Phase 1) must be in place first.

---

## IDEA-015 — Persistent alert feed panel in MFIP command bar

**Status:** PROPOSED
**Added:** 2026-05-11
**Source:** Dashboard reference docs review (session 2026-05-11)

**The idea:**
Add a collapsible alert feed panel to the MFIP dashboard command
bar. Shows last 10 Security Council events with: timestamp,
severity tier (INFO / WARNING / CRITICAL), agent source, message,
and an acknowledge button per alert. Currently alerts are only
visible as header badge counts (0 CRITICAL / 1 WARNING) with no
log surface.

**Why it fits:**
The Security Council three-tier alert system (06_SECURITY_COUNCIL.docx)
already defines the alert schema. The feed is the natural UI surface
for that output. Acknowledged alerts move to a separate archive
view, keeping the active feed clean.

**Build note:**
In Dash v1 this is a dcc.Store + callback pattern — alert state
lives in the store, the panel reads from it. The append-only
Security Log (flat file or DuckDB table) is the data source.

**Start criteria:**
Security Council agents are in training mode and writing to the
Security Log. Dashboard shell (Phase 1) must be in place first.

---

## IDEA-016 — Claude Code migration with Frontend Design and Trail of Bits skills

**Status:** PROPOSED
**Added:** 2026-05-11
**Source:** Conversation on spec-kit and Claude Code Skills (session 2026-05-11)

**The idea:**
Migrate MFIP development from the Claude project chat interface to
Claude Code (CLI agent with installable Skills), gated on reaching
the agent build phase. Two specific Skills are the trigger for the
migration: Frontend Design (production-grade UI discipline, replaces
generic AI dashboard aesthetics) and Trail of Bits Security (static
analysis on the codebase using Trail of Bits' methodology — direct
educational fit with the Security Council's stated learning purpose).

**Why it fits:**
- Phase 3+ of the build sequence (extraction, validation, modelling
  agents) is where Claude Code's filesystem access, slash commands,
  and SKILL.md format start to earn their place. Writing many
  structured agent prompts and running real code in the same loop
  is exactly what Claude Code is built for.
- Frontend Design addresses the dashboard polish problem directly.
  Caveat: the skill is React/Tailwind-focused; benefit in Plotly Dash
  is the design-thinking discipline (typography, spacing, hierarchy,
  colour), not direct code generation. Larger payoff if combined
  with the web-first frontend migration (IDEA-012).
- Trail of Bits Security teaches static-analysis security review
  patterns through use — aligned with the deliberate learning
  purpose of the Security Council in v3.

**The case against:**
- Switching cost is real: different interface, different file
  conventions, the project library (00–07 docx) doesn't transfer
  cleanly, shared chat context resets.
- The other eight skills on the list are either dangerous for a
  finance pipeline (Self-Healing auto-patches errors that should
  halt and surface), irrelevant to the stack (Figma-to-Code,
  MCP Builder), premature (Cost Reducer, Skill Creator), already
  covered by existing system prompt and decisions.md discipline
  (Superpowers), or only mildly useful (Researcher, Webapp Testing).
- Phase 1 (dashboard shell) and Phase 2 (Bloomberg ingestion and
  data layer) do not benefit enough from the migration to justify
  the disruption mid-build.

**Reference implementation:**
`nexu-io/open-design` (https://github.com/nexu-io/open-design) is the
open-source reference implementation for the Frontend Design skill
concept. It ships 31 `SKILL.md` design skills and 72 portable
`DESIGN.md` design systems — including Linear, Vercel, and Stripe —
following the same Claude Code `SKILL.md` convention MFIP would adopt.
When IDEA-016 comes up for approval at Phase 3, clone the repo and read
two files before deciding:
- `design-systems/linear-app/DESIGN.md` — token-level implementation of
  MFIP's dark-mode restraint benchmark.
- `skills/dashboard/SKILL.md` — production conventions for data-dense
  desktop dashboard layouts.
Do not install or run the stack. Read the files as reference only. The
frontend is React/Tailwind; code does not transfer to Plotly Dash. The
value is design discipline, not generated components.

**What needs to be true before APPROVAL:**
1. Phase 1 and Phase 2 are complete — dashboard shell working,
   Bloomberg export ingestion functional, data layer stable.
2. About to start Phase 3 (agent build) — the trigger condition.
3. Mac Mini M4 acquired (autumn 2026) OR Windows Claude Code
   workflow validated as acceptable.
4. IDEA-012 (web-first frontend migration) evaluated alongside
   this — the two decisions interact. If IDEA-012 is approved,
   Frontend Design's payoff is much larger; if rejected, payoff
   is more modest.

**If approved, affects:**
- Working environment, not architecture — no docx in the
  project library needs rewriting.
- `decisions.md` — new entry documenting the migration with
  Skills installed and rationale.
- New convention: agent prompts written as `SKILL.md` from the
  agent build onward, regardless of whether the Skills runtime
  is used (portable format, zero extra cost).

**Firewall check at decision time (2026-05-11 addendum):**
When IDEA-016 comes up for APPROVAL, the discussion explicitly asks
"what does this teach for MFIP specifically?" If the answer is primarily
a general analytical or methodological pattern rather than something
MFIP-specific, MFIP-Claude flags it as transferable without naming
dissertation relevance. Magnus routes manually to
`C:\Dissertation\inbox\transferable_from_mfip.md` from the Dissertation
Claude project. MFIP-Claude never writes to the dissertation inbox.
This guards against the "deliberate learning purpose" framing being
used to pull dissertation-relevant content into MFIP scope.

**Revisit date:** Start of Phase 3 — no earlier.

---

## 2026-05-10 — Claude Code settings.json permissions hardening

**Idea:** Add `.claude/settings.json` to the local repo with an explicit deny
list enforcing credential protection and destructive-command guards at the
Claude Code tool-permission level — not via `CLAUDE.md` instructions alone.

**Reference:** LeadGenMan `.claude` folder guide.

**Rationale:** `CLAUDE.md` instructions are advisory — Claude Code reads them
and is expected to comply. `.claude/settings.json` deny rules are enforced at
the tool-permission gate. The former is a norm, the latter is a guard. The
current setup relies on the norm alone, which is acceptable for an attentive
operator but means a Claude Code bug, a prompt injection from a fetched file,
or a sleepy late-night session is not blocked from reading `.env` or running
destructive commands. Defence in depth costs nothing here.

Specifically protective for MFIP because `.env` contains:
- Gmail SMTP creds (used by `mfip_alerts.py`)
- B2 backup credentials (`MFIP_B2_KEY_ID`, `MFIP_B2_APP_KEY`, `MFIP_RESTIC_PASSWORD`)
- Future Anthropic API key when modelling agents come online (Phase 5+)
- Future NewsAPI key when News Agent comes online

Any one of these leaking into a commit, a log, or a chat upload is a bad day.

**Built deny list (committed 2026-05-11 in feat/claude-config-deny-list, PR #4):**
```json
{
  "permissions": {
    "deny": [
      "Read(.env)",
      "Read(.env.*)",
      "Bash(rm -rf *)",
      "Bash(git push --force *)"
    ]
  }
}
```

**Wider deny categories deferred for future expansion:**
- Credential file reads beyond `.env` (Windows Credential Manager paths,
  `~/.aws/credentials`, `~/.ssh/*`, browser cookie stores).
- Network exfiltration patterns (`Bash(curl * | sh)`, `Bash(wget * -O -)`).
- Disk-destructive commands beyond `rm -rf` (`Bash(* > /dev/sd*)`,
  `Bash(format *)`, `Bash(diskpart *)`).
- Git history rewrites beyond force-push (`Bash(git config --global *)`,
  `Bash(git filter-branch *)`, `Bash(git reset --hard origin/*)`).

**Status:** `GRADUATED` — built and committed as `f76f6d9` (PR #4) on 2026-05-11.
Live record in `decisions.md`.

**Decision gate:** N/A — graduated.

---

## 2026-05-10 — Project Dashboard View (build progress, operational stats, task tracking)

**Idea:** A dedicated project dashboard screen — separate from the analysis
dashboard — showing MFIP's own build and operational health. Accessible as a
home screen or persistent tab before a company analysis is selected.

**Rationale:** The current spec treats Zone 1 (Command Centre) as a pipeline
status bar for analysis operations. But MFIP also needs a place to see the
project itself: which build phase is active, what tasks are pending, recent
decisions, backup status, last Bloomberg export date, and a direct link to the
GitHub repo. This is the screen Magnus opens when sitting down to work on MFIP,
not when doing analysis with it. Two distinct contexts; potentially two
distinct views.

**Open design questions:**
- Is this a separate tab/route (e.g. a "Home" screen) or an expanded Zone 1?
- What operational stats matter most: last pipeline run, last backup, last
  Bloomberg export, agent error rate, DuckDB log row counts?
- Should it show the current build phase checklist from `04_BUILD_SEQUENCE.docx`
  rendered live, or just a summary?
- Should it link out to GitHub, decisions.md, ideas.md directly?
- Does it replace the analysis view on startup, or sit alongside it?

**Architectural implication:** If "separate route" wins, the Phase 1 shell needs
a routing layer (`dcc.Location` + page registry pattern) from the start. If
"expanded Zone 1" wins, the existing Phase 1 spec mostly stands. This
distinction affects two of the four pre-Phase-1 micro-decisions
(`scripts/dashboard/` vs `dashboard/` folder structure, single-file vs split
callbacks) — they cannot be resolved until this is.

**Inspiration sources to explore:** Linear's project board aesthetic, Vercel's
deployment dashboard, GitHub's repository overview page. These are modern,
data-confident, dark-mode interfaces that handle operational status elegantly.

**Status:** `RESOLVED-PARTIALLY` — destination resolved, contents open.
The 2026-05-13 routing architecture decision in `decisions.md` resolves
the destination question: separate `/home` route wins, registered via
`pages/home.py`. Analysis moves to `/analysis`. Zone 1 is a component
of `/analysis`, not a separate page.

Open: what `/home` actually shows. The original brainstorm questions
(operational stats? build phase checklist? GitHub links? replace
analysis on startup?) are unresolved. Home currently ships as a stub
with placeholder content. Real Home contents are deferred to a future
session once `/analysis` is in real use and the operational view's
job is clearer.

**Decision gate:** Home contents — design TBD. Revisits when
`/analysis` has been in real use for at least a session and the
contrast between "analysis surface" and "operational surface" is
concrete enough to design from. If Home contents land, document the
design choice in a follow-up `decisions.md` entry referencing the
2026-05-13 routing architecture decision.

---

## 2026-05-10 — Dashboard visual identity: modern over terminal-inspired

**Idea:** Revise the design philosophy in `05_DASHBOARD_SPEC.docx`. Current
language is "Bloomberg meets modern UI" — but Bloomberg Terminal is an actively
bad UX reference. The target should be: modern fintech aesthetic, data-dense
but approachable, dark-mode first.

**Rationale:** Bloomberg Terminal's layout is a product of 1980s constraints
and institutional inertia, not good design. It optimises for information
density at the expense of everything else. MFIP is a personal tool Magnus uses
for deep work — it should feel enjoyable and fast to read, not like a
professional obligation. Better references: Robinhood (clean data hierarchy),
Linear (dark mode done right, excellent information density without clutter),
Vercel dashboard (operational stats presented with clarity), and modern
financial data tools like Koyfin or Finchat.

**Proposed design direction:**
- Retain the existing colour palette — it is already good (`#0D1117` background,
  JetBrains Mono for numbers, Inter for labels).
- Prioritise whitespace and visual breathing room over maximum density.
- Cards with clear hierarchy: primary number large, context small beneath it.
- Subtle borders and depth (box shadows) to separate zones rather than hard
  dividers.
- Status indicators that feel alive: animated pulse for active pipeline, smooth
  colour transitions for state changes.

**Inspiration sources to explore:**
- Koyfin (koyfin.com) — closest modern analog to what MFIP should feel like
- Finchat (finchat.io) — clean AI-native financial interface
- Linear (linear.app) — benchmark for dark-mode product design
- Vercel dashboard — operational stats done cleanly
- Dribbble/Behance search "financial dashboard dark mode" filtered for
  data-dense layouts, ignoring decorative-only results

**Status:** `GRADUATED` — visual identity locked in Session 4 (2026-05-11).
`05_DASHBOARD_SPEC.docx` v1.2 replaced the Design Philosophy and Colour Palette
sections with a coherent Visual Identity block: Koyfin-anchored, Finchat-informed,
Linear-restrained stance; both dark and light theme token sets defined from start;
typography rule narrowed to mono only where digits are scanned vertically; three-tier
density (Tight / Comfortable / Roomy); motion stance default-instant with reduced-motion
respected. Live record in `decisions.md` 2026-05-11 entry "Visual identity locked:
Koyfin-anchored, dual-mode from start, narrowed mono rule".

**Decision gate:** N/A — graduated.

---

## 2026-05-10 — Analysis results presentation: structure and layout TBD

**Idea:** Zone 2 currently describes what data to show but not how to structure
the reading experience — how a user moves from recommendation to thesis to
valuation to FSA, and what the information hierarchy feels like in practice.

**Rationale:** Zone 2 currently lists panels (2A Recommendation Card, 2B
Valuation Summary, 2C Thesis, 2D FSA Heatmap, 2E Download Bar) but the spatial
and interaction design is unresolved. Open questions: Is the reading flow
top-to-bottom or tabbed? Does 2A stay pinned while 2B–2E scroll? Can panels
expand to full-screen for deep dives? How does the FSA heatmap behave at
different window sizes? Needs a deliberate design pass with reference material
before Phase 5 builds the real data wiring.

**Open design questions:**
- Top-to-bottom scroll vs tabbed sections vs expandable cards?
- Which elements are always visible vs on-demand?
- How does expanding a valuation card (2B) interact with the rest of the
  layout?
- What does an "empty state" look like when no analysis has run yet?

**Inspiration sources to explore:**
- Analyst report PDF layouts — how sell-side structures the reading journey
  from summary to detail (Goldman, Morgan Stanley one-pagers are good
  references)
- Koyfin company page — modern equivalent of Zone 2
- How good news apps (Bloomberg app, FT app — not Terminal) handle progressive
  disclosure of detail

**Status:** `BACKLOG` — design resolution required, but not blocking Phase 1.
Phase 1 shell will use placeholder layout per current Zone 2 spec; this needs
resolution before Phase 5 wires real data.

**Decision gate:** Before Phase 5 (analysis wiring). Phase 1 shell can use
placeholder layout; design pass scheduled in the run-up to Phase 5.

---

## 2026-05-10 — Portfolio overview: balances, allocation, and performance display TBD

**Idea:** Zone 4 specifies a holdings table and risk metrics but the portfolio
visualisation — balances, allocation weights, performance curves, and
strategy-level views — is not designed yet.

**Rationale:** The four portfolio strategies (Core Long-Term, Active Short-Term,
Conservative Income, Alpha Fund) each have distinct characteristics that may
warrant distinct visual treatments. A single AG Grid table may not be the right
primary surface — a strategy-level summary with drill-down into holdings could
be more useful. Additionally, the performance curve (portfolio value over time)
and benchmark comparison are missing from the current spec entirely.

**Open design questions:**
- Should Zone 4 show all four strategies simultaneously or one at a time with
  a strategy selector?
- Is a portfolio value curve (time series chart) needed in Zone 4, or accessible
  via drill-down only?
- How are cash positions and uninvested allocation shown?
- What does Zone 4 look like when a portfolio has zero holdings (early build
  state)?

**Inspiration sources to explore:**
- Robinhood portfolio view — clean equity curve + holdings list
- Interactive Brokers' modern web interface (not the classic TWS) — handles
  multi-portfolio well
- Finchat portfolio tracker
- Any well-designed personal finance app that handles multiple "buckets"
  (e.g. YNAB's account structure, not its budgeting metaphor)

**Status:** `BACKLOG` — design resolution required, but not blocking Phase 1.
Phase 1 placeholder can be a static AG Grid table; design pass needed before
Phase 8.

**Decision gate:** Before Phase 8 (portfolio layer build). Zone 4 placeholder
in Phase 1 stands; design resolution scheduled in the run-up to Phase 8.

---

## 2026-05-10 — Dashboard UX inspiration: systematic collection before Phase 1 build

**Idea:** Before building the Phase 1 shell, spend one focused session
collecting and annotating reference screenshots covering five design domains
MFIP needs: (1) overall layout and zone structure, (2) data cards and number
hierarchy, (3) charts and time series, (4) tables and grids, (5) status/alert
surfaces.

**Rationale:** The Phase 1 principle is "build the shell with placeholder data
before any agents exist — design the end state first, build toward it." That
principle is right but requires knowing what the end state looks like. A
reference collection session before coding is a 1–2 hour investment that
prevents weeks of retrofitting.

**Proposed approach:**
- Koyfin and Finchat: free accounts, screenshot company pages and portfolio
  views
- Linear: free account, screenshot project board and issue list
- Vercel: free account, screenshot deployment dashboard
- Dribbble search "financial dashboard dark" — screenshot 5–10 that feel right,
  annotate what specifically works
- Store references in `C:\MFIP\design-refs\` (gitignored — binary files)
- Bring annotated references into the visual-identity and project-dashboard
  design sessions for grounded discussion

**Status:** `PAUSED` — collection started in Session 4.5 (2 raw screenshots
captured: Vercel projects-overview, Koyfin watchlist+charts dashboard, no
annotations) then paused as Session 4.5 closeout action. Per the 2026-05-11
Phase 1 routing decision in `decisions.md`, the project-dashboard architecture
session this collection was prep for is itself deferred until after Phase 1
foundation is built. References return when they can be calibrated against
real Plotly/AG Grid output — annotating reference screenshots before having
any concrete rendering to compare them to was assessed as the wrong activity
for Magnus's experience level (first project) and project state (zero code
shipped after four design sessions). Files live in `C:\MFIP\design-refs\`
(gitignored).

**Decision gate:** Resumes after Phase 1 foundation is built (estimated
Session 6–7), when reference quality can be calibrated against real working
code. Magnus-side prep, ~1–2 hours, not blocking subsequent build sessions.

---

## 2026-05-10 — Exploration areas log: five domains where outside inspiration is actively sought

**Idea:** Maintain a running record of the five areas where external ideas and
references are most valuable to MFIP, so incoming material can be assessed
against them deliberately.

**The five areas:**
1. **Dashboard UX and data visualisation** — chart types, layout patterns,
   information hierarchy, modern fintech aesthetic.
2. **Prompt engineering for financial agents** — structuring prompts for
   consistent JSON output, avoiding hedged analyst-speak, getting useful Chief
   Analyst theses.
3. **Financial analysis methodology** — DuPont depth, Beneish weighting by
   sector, what a useful Comps output actually looks like; MSc and CFA material
   applies.
4. **Pipeline resilience and error handling** — retry logic, graceful
   degradation, partial-data dashboard states; DevOps/MLOps patterns.
5. **Agent output testing and evaluation** — golden-set testing, LLM output
   evaluation frameworks, regression testing for financial models.

**Rationale:** Keeps the filter explicit. When Magnus encounters content that
might be relevant, checking it against these five areas produces faster, more
useful assessments than open-ended "is this relevant to MFIP?" evaluation.

**Status:** `REFERENCE` — this entry is a permanent anchor, not a buildable
feature. Stays here as a stable reference; revisit and update if a sixth domain
emerges or if an existing one closes (e.g. once dashboard UX is fully resolved
post-Phase-1, that domain may narrow or retire from the list).

**Decision gate:** None — reference entry. Revisit the list quarterly or when
a domain materially changes status.

---

## 2026-05-14 — DESIGN.md token audit before theme.py

**Status:** `REFERENCE`
**Added:** 2026-05-14
**Source:** open-design repo review (session 2026-05-14)

**The idea:**
Before writing `theme.py`, read two `DESIGN.md` files from the
`nexu-io/open-design` repo (https://github.com/nexu-io/open-design):
- `design-systems/linear-app/DESIGN.md` — Linear's token-level
  implementation: colour, typography, spacing, component patterns,
  motion stance, and anti-patterns. Linear is MFIP's explicit
  benchmark for dark-mode restraint.
- `design-systems/vercel/DESIGN.md` — Vercel's implementation of
  operational stats presented with clarity. MFIP's benchmark for
  Zone 1 (Command Centre) and Zone 4 (Portfolio View).

Cross-reference against the Visual Identity block in
`05_DASHBOARD_SPEC.docx` to surface any gaps before coding starts.
One-time read, ~30 minutes. No installation required — clone the repo
and open the two files.

**Rationale:** `05_DASHBOARD_SPEC.docx` names Linear and Vercel as
design benchmarks but does not encode their token-level decisions.
Reading the canonical `DESIGN.md` files before writing `theme.py`
closes that gap while it is still cheap to close.

**Decision gate:** Before `theme.py` is written in Phase 1. No later.

---

## IDEA-028 — Chief Analyst discovery form pattern

**Status:** `PROPOSED`
**Added:** 2026-05-14
**Source:** open-design repo review (session 2026-05-14)

**The idea:**
Apply Open Design's "turn-1 discovery form" pattern to the Chief
Analyst agent prompt design. In Open Design, every design brief begins
with a structured question form that locks down ambiguous inputs
(surface, audience, tone, brand context, scale) before the model
produces a single artifact. The equivalent for the Chief Analyst is a
structured Pydantic input model that validates and resolves ambiguous
context — investment horizon, applicable portfolio strategies, risk
tolerance framing — before the recommendation is generated.

**Why it fits:**
The Chief Analyst currently receives a fixed input schema and produces
a BUY/HOLD/SELL recommendation. Unstated assumptions about horizon or
portfolio applicability can cause the recommendation to be correctly
argued but wrong for the intended use. Enforcing a pre-flight
validation step — in code, not in the prompt — reduces the surface area
for the Chief Analyst to reason from implicit context. This is a prompt
engineering and schema design idea, not a UI idea.

**The case against:**
- The input schema (Chief Analyst's Pydantic model) may already be
  specific enough in practice. This is a hypothetical problem until
  the agent is built and tested.
- Adds a validation step that could be over-engineering for a personal
  tool with a single known user.

**Decision gate:** Phase 7 (Chief Analyst build). Evaluate whether
input ambiguity is a real problem in practice before implementing.
If the first 10 test recommendations are coherent without it, skip.

---

## 2026-05-14 — Public APIs directory as reference resource

**Status:** `REFERENCE`
**Added:** 2026-05-14
**Source:** Session discussion (2026-05-14)

**The idea:**
Keep the public-apis GitHub repository
(https://github.com/public-apis/public-apis) as a standing reference
for free API integration across both MFIP and the personal scheduler
project.

**MFIP — News Agent feed:**
The News Agent needs a real-time news feed. Free financial news APIs
(e.g. NewsAPI, Finnhub news endpoint) are a clean, low-friction source
for that layer. Bloomberg is the data spine for market and financial
statement data and that does not change — but news feed is a separate
concern and a public API fits it well. Worth evaluating when the News
Agent is built in Phase 3+.

**MFIP — Post-Bloomberg data layer (long-term):**
Bloomberg Terminal access ends with the MSc. When it does, the manual
export workflow at the Kingston lab becomes impossible. A financial
market data API (e.g. Alpha Vantage, Finnhub, polygon.io) could
eventually replace the Bloomberg export templates and automate the data
gathering operation entirely — removing the manual lab step and making
MFIP self-sufficient. This is a significant architectural change and is
firmly v2+ territory, but worth keeping the Bloomberg data layer
cleanly abstracted so the swap is not painful when the time comes.

**Personal scheduler project:**
The repo's calendar, weather, and translation/language sections are
worth consulting when that build starts. Not an MFIP concern.

**Decision gate:** None — reference entry. Consult when News Agent
build begins (Phase 3+) and when Bloomberg access sunset becomes a
planning horizon.

---

## 2026-05-14 — dotclaude as .claude/ structure reference

**Status:** `REFERENCE`
**Added:** 2026-05-14
**Source:** Session tool review (2026-05-14) — github.com/poshan0126/dotclaude

**What it is:**
A standardised `.claude/` folder template for Claude Code projects. Ships
a full structure: `CLAUDE.md` project instructions, modular `rules/` files
(code quality, testing, database safety, error handling, security), a
`settings.json` / `settings.local.json` split, and a 14-plugin marketplace
including `code-reviewer`, `security-reviewer`, `debug-fix`, `tdd`, and
`ship`.

**What is already covered:**
The `settings.json` / `settings.local.json` split mirrors what MFIP already
built in PR #4 (IDEA graduated, `decisions.md` 2026-05-11). No action needed.

**What is worth keeping:**

1. **`rules/` contextual loading pattern** — modular instruction files that
   load near relevant files (e.g. `database.md` near migration files,
   `security.md` near API and auth files). This is the modular SKILL.md
   convention IDEA-016 is evaluating. When IDEA-016 comes up for APPROVAL
   at Phase 3, clone this repo and read `rules/security.md` and
   `rules/error-handling.md` alongside the open-design reference files.
   The two repos together (open-design for design discipline, dotclaude for
   code discipline) are the full reference set for the IDEA-016 decision.

2. **`ship` plugin** — full commit-to-PR workflow with per-step confirmation:
   scans changes, stages files (skipping secrets, locks, and build output),
   drafts a commit message in the repo's style, pushes, and opens a PR.
   Potentially useful now, regardless of IDEA-016 outcome. Evaluate at the
   start of the next Claude Code session.

**Decision gate:** IDEA-016 approval (Phase 3). Read `rules/` files as
reference alongside open-design. `ship` plugin can be evaluated earlier —
no phase gate.

---

## IDEA-017 — Design-session budgets (operational discipline)

**Status:** APPROVED
**Added:** 2026-05-11
**Source:** Session 3 risk assessment (Concern 1)

**The rule:**
Each pre-Phase-1 design session has a hard time budget. If a session
runs over, ship a "good enough" answer and move on rather than refining
indefinitely.

- Visual identity session: 1 session, output is a ~200-line revision to
  `05_DASHBOARD_SPEC.docx` Design Philosophy section. No second pass.
- Project Dashboard architecture session: 1 session, output is a single
  decision (Home screen vs expanded Zone 1) plus a routing-layer sketch
  if Home wins.
- UX inspiration collection: Magnus-side prep, 1–2 hours, not a Claude
  session.

**Rationale:**
Pre-Phase-1 work has accumulated to four design-decision sessions plus
Magnus's prep before Phase 1 build can start. Each session feels
productive in isolation. None produces code. Without a budget, the
pattern is: visual identity stretches to two sessions, project dashboard
stretches to two, suddenly six sessions in and Phase 1 hasn't started.
Doc passes and design refinement are infinitely refinable; code work is
the only thing that closes them.

**Mechanism:**
At the start of each pre-Phase-1 design session, MFIP-Claude reminds
Magnus of the session's budget and intended output. If a session ends
without that output produced, the question is "ship what we have or
spend another session?" — and the default answer is ship.

**Decision gate:** Applies from Session 4 onward, until Phase 1 build starts.

---

## IDEA-018 — decisions.md index / compaction pass

**Status:** GRADUATED — see `decisions.md` 2026-05-14 entry "decisions.md indexing: single-file TOC + inline tags supersedes separate index file"
**Added:** 2026-05-11
**Source:** Session 3 risk assessment (Concern 2)

**The idea:**
When `decisions.md` exceeds 40 entries, introduce a navigation surface.
Two options to evaluate at that point:

1. **Index file** — `decisions_index.md` alongside `decisions.md`, listing
   every entry by date with a one-line summary and tags (architecture /
   build / cleanup / agent / infrastructure). Canonical record untouched;
   index adds searchability.
2. **Compaction pass** — periodically (quarterly?) consolidate related
   closeout entries into a single summary, archiving the originals to
   `decisions_archive.md`. Compresses the active doc while preserving
   history.

**Rationale:**
`decisions.md` is growing steadily. Each new entry is well-formed and
properly structured, but the cumulative effect is a long document where
searching depends on keyword luck. The 2026-05-09 cleanup pass found
seven gaps in one sweep — accrued drift from a growing doc set is a
known failure mode. Without navigation, future sessions (including
Claude Code sessions) will start missing decisions because they're
buried.

**Why now is too early:**
Current entry count is ~20. The cost of building an index now is
similar to the cost of building one at 40 entries, but the benefit is
lower because the doc is still scannable end-to-end. The 40-entry
threshold is a guess; calibrate when we hit it.

**Decision gate updated:** 2026-05-13 — gate brought forward from "~40 entries"
to "end of Phase 1 / before Phase 2 kickoff." Index pass confirmed as the
chosen method (option 1: decisions_index.md). Compaction deferred until
the index proves insufficient. Schedule as a Phase 1 close-out task alongside
IDEA-023 and IDEA-027.

---

## IDEA-019 — V1 Definition of Done

**Status:** APPROVED with decision gate
**Added:** 2026-05-11
**Source:** Session 3 risk assessment (Concern 4)

**The idea:**
Before Phase 1 build kickoff, produce an explicit V1 definition-of-done
document. Closes the scope of v1 so that subsequent ideas have a clear
home (in v1 or not).

**The problem:**
There is currently no explicit "MFIP v1 is done when…" statement.
Implicit criteria can be inferred (all 21 agents built, 6 companies
covered, dashboard functional, 4 portfolio strategies populated) but
they are never stated as a checklist. Several decisions reference
"v1 stable on 6 companies for 30+ days" as a revisit trigger for v2
items — that is a use-time gate, not a build gate.

Without a `done` line, scope creep is structurally invited. Every new
idea since the project started has either entered v1 (Earnings Quality,
Thesis Monitor, validator, branch protection, settings.json hardening,
four design sessions, five 2026-05-11 dashboard elements…) or been
deferred. The deferred items have decision gates. The v1-adopted items
do not have a closing gate.

**Proposed output:**
Either a section in `00_PROJECT_OVERVIEW.docx` or a new
`V1_DEFINITION_OF_DONE.docx` listing the closed scope as a checklist.
After publication, the rule is: new items go to `ideas.md` as BACKLOG,
not into v1.

**Why the right moment is end of pre-Phase-1 design sessions:**
The pre-Phase-1 design queue (visual identity, project dashboard
architecture) will produce additions to Phase 1's scope. Definition of
done should be drafted *after* those decisions land, so visual identity
+ project dashboard + the 2026-05-11 dashboard additions are baked in
and the line is drawn cleanly. Drafting it now would lock the wrong
boundary.

**Decision gate:** End of pre-Phase-1 design sessions, before Phase 1
build kickoff. Output: published definition of done + commitment that
post-publication, new items default to BACKLOG.

## IDEA-020 — Scrapling as web fetcher for News Agent and Macro Agent

**Status:** PROPOSED
**Added:** 2026-05-11
**Source:** Session discussion — Scrapling library review

**The idea:**
Add [Scrapling](https://github.com/D4Vinci/Scrapling) as an optional fetcher in the
News Agent and Macro Agent for sources that are Cloudflare-protected or that break
silently on HTML redesigns. Scrapling is a Python web scraping framework that combines
HTTP fetching, Cloudflare bypass (via Camoufox, a patched Firefox), and adaptive
element tracking — elements are fingerprinted using multiple DOM signals so that when
a site's HTML structure changes, the selector still resolves without manual updates.

**Why this was raised:**
The News Agent pulls from RSS feeds (feedparser) and NewsAPI. For sources without
clean RSS — company IR pages, Oslo Børs announcements, LSE regulatory pages, FT — a
standard `requests` call either fails on Cloudflare or breaks silently when the page
is redesigned. Scrapling's adaptive tracking solves the silent-breakage problem.
The Macro Agent has the same exposure for central bank announcement pages (Norges
Bank, BoE, Fed) that pandas-datareader cannot reach directly.

**Where it fits:**

| Agent | Use case | Fetcher |
|---|---|---|
| News Agent | IR pages and news sources without RSS; Cloudflare-protected financial news | `StealthyFetcher` for CF-protected sites; `Fetcher` for standard HTTP with adaptive tracking |
| Macro Agent | Central bank announcement pages when pandas-datareader fails | `Fetcher` or `StealthyFetcher` as fallback |

**Where it does NOT fit:**
- Annual report PDFs: the extraction pipeline ingests local files via camelot-py and
  pymupdf. Scrapling is a web scraper; it adds nothing to local PDF parsing. The act of
  acquiring PDFs is a manual step by design (durable artefacts, 6 downloads per year).
- Bloomberg data: no web scraping involved — structured Excel export workflow.

**Scrapling's differentiating feature for MFIP:**
Adaptive element tracking. Selectors fingerprint DOM elements using tag, attributes,
text content, and sibling position simultaneously. When a site redesigns its HTML,
elements are relocated automatically. This is the primary value for MFIP — financial
IR pages and news sites redesign regularly, and silent selector breakage is exactly
the failure mode that produces undetected data gaps in the News Agent.

**Dependencies and cost:**
- `pip install "scrapling[fetchers]"` + `scrapling install` (downloads Camoufox and
  Playwright browsers — ~500MB, one-time)
- Python 3.9+ required (compatible with MFIP's Python 3.12 environment)
- `StealthyFetcher` only needed where Cloudflare bypass is required — `Fetcher` alone
  is a lightweight alternative with no browser dependency

**Not a core dependency in v1:**
The current stack (feedparser + NewsAPI) is sufficient for the Phase 1–5 build. This
is an enhancement to the News Agent and Macro Agent's fetching resilience, not a
prerequisite for any agent. Phase 5 (Intelligence Layer) is the earliest point it
becomes relevant.

**Decision gate:** Phase 5 build start. Evaluate then whether feedparser + NewsAPI
cover all required sources, or whether Scrapling is needed for specific IR pages or
Cloudflare-protected sources that cannot be reached otherwise. If adopted, add to
`requirements.txt` and document the per-source fetcher choice in `config/news_feeds.yaml`.
If feedparser + NewsAPI prove sufficient in practice, this entry stays PROPOSED indefinitely.

## IDEA-021 — MAX date preset: wire to earliest available data date

**Source:** Session 6 Part 2 build.

**Context.** Zone 1's Global Date Filter has a MAX preset button. Spec
says "MAX — all available data" without a numeric bound. Current
implementation in `zone1.py` uses 20 years back from today as a
placeholder.

**Action.** Once Bloomberg / Excel data loaders land (Phase 2+), wire
the MAX preset to compute "earliest data date across the loaded
universe" rather than a hardcoded 20-year window. Likely lives in the
date-range-store's initial-value computation or a callback that
resolves "MAX" against the data layer.

**Status:** PROPOSED. Decision gate: end of Phase 2 (when data loading
is real).

## IDEA-022 — External tool review: Obscura, OpenSpace, awesome-claude-skills

**Status:** REFERENCE
**Added:** 2026-05-12
**Source:** Session tool review — six external resources assessed against MFIP

Six items were reviewed and assessed for MFIP applicability. Three produced
findings worth retaining. Three were discarded outright (wrong tech stack or
irrelevant). Findings are recorded here at the correct phase for each.

---

### Finding A — Obscura headless browser (Phase 5 / v2 PDF fetcher)

**What it is:**
[Obscura](https://github.com/h4ckf0r0day/obscura) — a Rust-based headless browser engine,
CDP-compatible with Playwright/Puppeteer. Single binary, ~30MB RAM per instance vs
~200MB for headless Chrome. Built-in stealth mode with fingerprint randomisation.
Build-from-source only (Rust 1.75+ required). Released April 2026, MIT licence.

**Why it was assessed:**
If MFIP ever needs browser-based web scraping, Obscura is a lighter drop-in for
headless Chrome. The v2 PDF fetcher (IDEA-008) targets SEC EDGAR (JSON API) and
European regulator pages first — most are structured sources. But some regulator
pages (Oslo Børs, LSE) may require JS rendering on dynamic content.

**Why not v1:**
v1 has no web scraping layer. Bloomberg data comes via Excel add-in.
Annual report PDFs are acquired manually. Scrapling (IDEA-020) already covers
the HTTP/Cloudflare fetching case for News and Macro agents. Obscura's value
is specifically JS-heavy pages where a full browser is unavoidable.

**When to revisit:**
v2 PDF fetcher build (IDEA-008 activation). If SEC EDGAR JSON API and
regulator static pages cover all sources, Obscura stays dormant. Activate
only if a required source requires JS rendering and Scrapling's `StealthyFetcher`
(Camoufox) does not cover it.

**Integration note:**
CDP-compatible — existing Playwright scripts can point at Obscura's server
with one line change (`connect_over_cdp("http://localhost:9222")`). Zero
code rewrite if adopted.

---

### Finding B — OpenSpace skill evolution concepts (Phases 3–7 / Prompt Library)

**What it is:**
[OpenSpace](https://github.com/HKUDS/OpenSpace) — a self-evolving skill engine for
AI agents. Agents capture successful execution patterns as versioned skills (FIX /
DERIVED / CAPTURED), share them via a cloud registry, and evolve them automatically
from post-execution analysis.

**Why it is NOT being adopted as a tool:**
OpenSpace's self-mutation is architecturally incompatible with MFIP. The Security
Council's value depends on the pipeline being observable and auditable. Agents that
silently rewrite their own behaviour would undermine this entirely. OpenSpace is
also designed for Claude Code / general-purpose agentic workflows, not a
Python pipeline inside a Dash desktop app.

**The concept worth keeping:**
The pattern of capturing successful execution workflows as reusable, versioned,
named definitions — and referencing them by name rather than re-deriving the
same reasoning each time — is the right abstraction. MFIP already implements
this via `PROMPT_LIBRARY.docx` (34 standardised prompts). The Prompt Library is
MFIP's equivalent of OpenSpace's skill registry, without self-mutation risk.

**Action:**
When adding new prompts to the Prompt Library at each build phase, explicitly
ask: "Is this a reusable pattern that will recur across multiple companies and
analysis cycles?" If yes, add it to the library as a named, versioned entry.
This is the OpenSpace insight without the OpenSpace risk.

**When to revisit:** At each agent build phase (Phases 3–7). No tooling change
required — this is a discipline note for Prompt Library maintenance.

---

### Finding C — awesome-claude-skills: three skills worth reading (Phases 1–6)

**What it is:**
[awesome-claude-skills](https://github.com/ComposioHQ/awesome-claude-skills) — a
curated registry of Claude Code skills. Mostly Composio SaaS automation (irrelevant
to MFIP). Three skills are worth reading at specific build phases.

**Skills to read:**

1. **`software-architecture`** (read at Phase 1 — dashboard shell build)
   Implements Clean Architecture and SOLID principles. Read before writing
   `mfip/dashboard/` module structure to ensure the theme, layout, and callback
   layers respect clean module boundaries from the start.

2. **`subagent-driven-development`** (read at Phase 4 — Extraction Layer build)
   Dispatches independent subagents with code review checkpoints between iterations.
   Directly relevant to how MFIP's Extraction Layer works: Extractor A and B run
   independently, output is reconciled by the Reconciliation Engine. The skill
   encodes patterns for structuring independent parallel agents and their handoff
   contracts. Read before writing the Extractor agent prompts.

3. **`root-cause-tracing`** (read at Phase 6 — Security Council build)
   Traces errors deep in execution back to their original trigger. Relevant to
   Security Council debugging and the Technical Officer's log analysis mandate.
   May inform the Security Log query patterns and the three-tier alert escalation
   logic.

**How to access:**
`git clone https://github.com/ComposioHQ/awesome-claude-skills` and read the
relevant `SKILL.md` files. No installation required — read for patterns, not
for execution in MFIP's environment.

---

### Discarded items (recorded for completeness)

- **Shannon AI Pentester** — penetration testing tool. MFIP has no network-exposed
  surface. Irrelevant.
- **"3 Free Tools" design guide** (shadcn / 21st.dev / UX Pro Max) — React component
  ecosystem. MFIP uses Plotly Dash. Wrong tech stack.
- **Drive design skills file** — auth-gated, could not load. Likely the same React
  component guide. Irrelevant regardless.

## 2026-05-12 — IDEA-023 — Served-layout callback ID resolution smoke test

**Idea:** A pytest smoke test that instantiates the Dash app and asserts
every callback's Input/Output IDs resolve against the served layout.

**Rationale:** Session 6 surfaced four Dash-3.x runtime failures
(`use_pages` + `page_container`, `suppress_callback_exceptions`,
explicit `layout=` kwarg, cross-layout Input validation) that all
passed structural pytest checks and only appeared on browser launch.
A served-layout resolution test would have caught all four at
pytest time.

**Status:** GRADUATED — implemented as `tests/test_served_layout.py` in PR #30.

**Update 2026-05-13:** Graduates from PROPOSED to APPROVED following
the three-strikes pattern documented in the 2026-05-13 routing
architecture decision in `decisions.md`. Session 7 Parts 1-3 each
surfaced test-passes-but-browser-fails defects (theme-toggle cross-
layout in Part 1; settings density wiring in Part 2; missing
Zones 2-4 from served DOM in Part 3). A served-layout smoke test
would have caught the Part 3 mismatch immediately at Part 1, and is
now the canonical defence against this failure mode.

**Decision gate:** Phase 1 close-out. Implement before merging the
final Phase 1 PR.
