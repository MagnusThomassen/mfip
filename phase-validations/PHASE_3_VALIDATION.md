# Phase 3 Validation

**Phase:** Bloomberg Ingestion
**Status:** In progress
**Started:** 2026-05-18 (Session 18 — kickoff)
**Completed:** N/A
**Validated by:** Magnus Thomassen
**Session:** 18 (kickoff) / [TBD] (close-out)

---

## Phase deliverables checklist

Derived from `04_BUILD_SEQUENCE.docx` Phase 3 entry. The 13
deliverables are grouped under five sub-headings for readability;
ordering within each sub-heading follows the build-sequence ordering.

### Architectural decisions (before code)

- [ ] Decide watchdog scope at Phase 3 build start — three options
  on the table given exports flow directly to `bloomberg_archive\`:
  (a) re-purpose watchdog to validate `bloomberg_archive\` directly,
  (b) introduce inbox usage as part of Phase 3 to gain
  format-quarantine benefits, (c) drop watchdog from v1 entirely.
  Decision logged in `decisions.md` before downstream Phase 3 code
  begins.
  - evidence: [`decisions.md` YYYY-MM-DD entry — TBD]

### Parser core

- [ ] Build Bloomberg Excel parser (openpyxl-based)
  - evidence: [PR #N / module path TBD]
- [ ] Skip CONFIG sheet during parsing — CONFIG is metadata
  (ticker, currency) retained for self-documentation, not data.
  Saved company workbooks have 8 sheets total (7 data sheets +
  CONFIG); the parser reads only the 7 data sheets.
  - evidence: [PR #N]
- [ ] Build currency derivation from ticker exchange suffix
  - evidence: [PR #N]

### Validation behaviour

- [ ] Implement validation against `07_BLOOMBERG_EXPORT_TEMPLATE.docx`
  contract. Foundation:
  `scripts/ingestion/validate_bloomberg_workbook.py` from Phase 0
  per `decisions.md` 2026-05-10 "Pre-Phase-3 Bloomberg saved-file
  validator". Phase 3 work is wiring the existing validator into
  the parser path and extending it where the parser surfaces
  validation needs the saved-file contract didn't cover (e.g.
  row-count sanity checks, null-density checks).
  - evidence: [PR #N — parser-validator wiring]
- [ ] Build sheet-name verification (soft validation in v1 —
  Advisory log entries for mismatches; tightens to quarantine in
  v2 per `07_BLOOMBERG_EXPORT_TEMPLATE.docx`)
  - evidence: [PR #N]
- [ ] Match RV_Comps columns by header name, not by column
  position. The column set is a terminal-side contract (saved as
  a named layout on the Bloomberg Terminal). Position-based
  matching breaks silently if the layout drifts.
  - evidence: [PR #N]
- [ ] Surface RV column-set drift as Advisory — when expected
  columns are missing or unexpected columns are present, log an
  Advisory entry rather than failing the file. The Comps Agent
  then handles missing multiples per its sector-appropriate
  selection logic (see `07_BLOOMBERG_EXPORT_TEMPLATE.docx` KNOWN
  DATA GAPS).
  - evidence: [PR #N — extends Phase 0 validator's
    `RV_COLUMN_DRIFT` / `RV_PLANNED_COLUMN_PENDING` Advisory
    behaviour per `decisions.md` 2026-05-10]
- [ ] Validate company workbooks against the seven required
  sheets: HP_Monthly, HP_Daily, DVD, BETA, EE, RV_Comps, ANR
  - evidence: [PR #N]
- [ ] Validate INDICES workbook contains all four required index
  sheets (OBX, OMXC25, UKX, SPX) and that each company's required
  index sheet is present
  - evidence: [PR #N]
- [ ] Validate FX workbook is present for the session date and
  contains all FX-cross sheets required by the companies in the
  package (NOKUSD for Norwegian tickers, DKKUSD for NOVO B,
  GBPUSD for CKN). Flag Advisory if missing in v1; tighten to
  quarantine in v2. Validate that pandas-datareader can resolve
  FX rates for the export date as a live-dashboard fallback
  check. Validate USD display currency on all sheets except BETA
  (BETA sheet must be in local currency — flag if USD detected).
  - evidence: [PR #N]

### Sector-specific handling

- [ ] Handle CKN GBp double conversion — CKN trades in GBp
  (pence), not GBP. Apply (1) detect CKN ticker, (2) divide
  price/target-price fields by 100 for the GBp → GBP unit step,
  (3) standard GBP → USD FX conversion via the FX workbook.
  Order matters; documented in `07_BLOOMBERG_EXPORT_TEMPLATE.docx`
  KNOWN DATA GAPS.
  - evidence: [PR #N]

### Documentation

- [ ] Document quarantine logic as the contract for when
  `bloomberg_inbox\` is re-activated. In v1, validation runs only
  when explicitly invoked (e.g. during Phase 3 development tests
  against archived files), not on every file landing — exports
  flow directly to `bloomberg_archive\` rather than through inbox
  quarantine. The quarantine contract documents how the same
  `validate_workbook()` function would be wrapped by a watchdog
  handler if `bloomberg_inbox\` is ever re-activated.
  - evidence: [PR #N — likely a `decisions.md` entry or a
    docstring block in `scripts/ingestion/validate_bloomberg_workbook.py`]

---

## Runtime artifacts verified on disk

To be confirmed during the Phase 3 validation walkthrough at end of
Phase 3 (close-out session — Session 18 or later, depending on lab
visit timing).

- [ ] Parser module importable from the codebase
  - [ ] verified existing
  - [ ] verified behaving correctly
  - notes: Module location TBD pending parser-shape decision in
    early Phase 3 PRs. Name is constrained: "Validator" is
    reserved per `CLAUDE.md` Terminology table for
    `scripts/ingestion/validate_bloomberg_workbook.py`; the new
    parser needs a distinct name. Verify by `python -c "import
    <module>"` returning 0 and by an interactive parse of a
    Git-versioned template producing the expected output shape.

- [ ] Parser unit tests pass
  - [ ] verified existing
  - [ ] verified behaving correctly
  - notes: Tests live under `tests/ingestion/...`. Verify by
    `python -m pytest tests/ingestion -q` returning a green run.
    Pre-lab test coverage uses the Git-versioned template workbooks
    at `templates/bloomberg/` as fixtures.

- [ ] Parser-validator wiring exercised end-to-end against a real
  Bloomberg export from `bloomberg_archive\<TICKER>\<DATE>\`
  - [ ] verified existing
  - [ ] verified behaving correctly
  - notes: **Lab-visit dependent.** Requires a fresh export
    generated at the Kingston Bloomberg trading lab against the
    Git-versioned templates. The 2026-05-08 EQNR_NO archive is the
    earlier reference workbook and may serve as a pre-lab smoke
    test, but the official Phase 3 exercise uses a lab-fresh
    workbook.

- [ ] First production `decision_log` row from a real parser
  invocation
  - [ ] verified existing
  - [ ] verified behaving correctly
  - notes: **Lab-visit dependent.** First production write to
    `decision_log` (table has been empty since schema creation per
    PHASE_2_VALIDATION.md). Verify via direct query:
    `SELECT row_seq, correlation_id, outcome FROM decision_log
    ORDER BY row_seq`. Row should carry a non-null `correlation_id`
    (parser invocation is a "pipeline run" by the working
    definition; correlation_id required on `decision_log` per
    `decisions.md` 2026-05-14).

- [ ] First `decision_log` row captured by the next nightly export
  cycle
  - [ ] verified existing
  - [ ] verified behaving correctly
  - notes: **Lab-visit dependent.** Closes the audit-trail loop
    established in Phase 2 PR-C — verifies the cursor-based export
    correctly picks up `decision_log` writes (which it has never
    had to do until Phase 3, since `decision_log` was empty
    throughout Phase 2's exercise). Verify by reading the JSON
    export file after the next 02:00 trigger:
    `Get-Content C:\MFIP\repo-logs-archive\exports\<YYYY-MM-DD>.json`
    contains the new `decision_log` row inside the `decision_log`
    array, and `C:\MFIP\runtime\export_state.json` reflects the
    advanced cursor.

- [ ] Watchdog scope decision recorded in `decisions.md`
  - [ ] verified existing
  - [ ] verified behaving correctly
  - notes: Verify by grep for the watchdog-scope entry in
    `decisions.md`. Implementation status of the chosen option is
    recorded in the entry itself; this artifact verifies only that
    the decision was made and committed, not that the chosen option
    is fully built (which is tracked under the relevant
    deliverable's `evidence:` line above).

---

## Live exercise log

Walkthrough to be run by Magnus at Phase 3 close-out. Phase 3 has a
structural pre-lab vs post-lab split; the live exercise log reflects
that.

**Section A — Pre-lab parser exercise**

- [date, action, observed result — TBD]

**Section B — Lab visit**

- [date, action, observed result — TBD]

**Section C — Post-lab parser invocation against fresh export**

- [date, action, observed result — TBD]

**Section D — Audit-trail loop closure**

- [date, action, observed result — TBD]

---

## Findings

### Working as intended

- [list TBD at close-out]

### Issues discovered (fixed in this session)

- [list TBD at close-out]

### Issues discovered (fixed in later sessions)

- [list TBD at close-out]

### Issues discovered (deferred)

- [list TBD at close-out — `worklog.md` YYYY-MM-DD entries or
  `ideas.md` entries]

---

## Sign-off

- [ ] I have personally walked through every deliverable and runtime
  artifact above and confirmed each one. New findings (if any) are
  logged in `worklog.md` or `ideas.md` per the boundary rule.

**Signed:** Magnus Thomassen
**Date:** [YYYY-MM-DD]
