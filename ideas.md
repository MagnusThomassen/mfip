# MFIP — Ideas Log

This file records ideas that have been raised, discussed, and deemed worth keeping
but not yet built. An entry here means: "this is interesting, well-formed enough to
act on later, and should not be lost or re-derived."

This file replaces V2_BACKLOG.docx, which has been retired. All five entries from
that document have been migrated here. The file lives in the repo alongside
decisions.md and follows the same Git versioning policy.

**Lifecycle of an idea:**

```
ideas.md (PROPOSED)
    → ideas.md (APPROVED — assigned to v1 build, pending doc update)
    → ideas.md (BACKLOG — confirmed deferred, start criterion defined)
    → decisions.md (when built and implemented)
```

**Status values:**
- `PROPOSED` — raised and discussed, not yet decided
- `APPROVED` — decided for v1, pending doc update and build phase assignment
- `BACKLOG` — decided as deferred; has a defined start criterion
- `GRADUATED` — built; entry archived here for reference, live record in decisions.md

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