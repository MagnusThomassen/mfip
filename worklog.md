# MFIP — Worklog

> In-flight observations and bug-shaped items that close within sessions or days.
> Sibling to `ideas.md` (forward-looking, phase-gated items) and `decisions.md`
> (architectural record). Established 2026-05-13 — see the
> `2026-05-13 — ideas.md splits into ideas.md + worklog.md` entry in
> `decisions.md` for rationale.

## Boundary rule

If an item's decision gate is measured in *phases*, it belongs in `ideas.md`.
If measured in *days* or "next session," it belongs here.

## Entry format

- Date-prefixed (no IDEA-NNN numbering)
- Statuses: `OPEN` / `CLOSED-<reason>` / `MOVED-TO-IDEAS`
- New entries appended at the bottom; closed entries stay in place as audit trail

---

## 2026-05-12 — Header rendering at 108px (originally IDEA-025)

**Status:** CLOSED-MISDIAGNOSED

**Observation (as originally logged):** Zone 1 header rendering at 108px
instead of the spec-defined chrome height. Diagnostic logged on the
`phase1/zone1-focus-diagnosis` branch (Session 7 Part 2 PR #14 work).

**Why misdiagnosed:** The 108px figure was the entire `body` element's
height, not the header. Zones 2-4 weren't in the DOM at all — only
Zone 1 was rendered, and Zone 1's own background tint filled the
viewport, which was misread as "header colour at unexpected height."
Architectural symptom, not a styling defect.

**Provenance:** Logged on PR #14 branch 2026-05-12; PR #14 was closed
without merging following the 2026-05-13 routing architecture decision.
Re-logged here as a tombstone for audit-trail completeness. Never
landed on `main`; not re-introduced.

**Resolves when:** `/analysis` route renders multi-zone layout per the
Session 8 routing restructure. The symptom dissolves with the
architectural fix.

---

## 2026-05-12 — Zone 1 focus ring not visible on non-native interactive elements (originally IDEA-026)

**Status:** CLOSED-PREMATURE

**Observation:** The `*:focus-visible` CSS rule established in PR #14
loads correctly and produces a visible focus ring on the company
selector (a native-focusable `dcc.Dropdown`). It does NOT produce a
visible ring on the settings cog, date filter preset buttons
(1Y/3Y/5Y/MAX/Custom), or alert badges. Three candidate causes were
identified during Session 7 Part 2:

1. The non-ringed elements aren't actually focusable — `<div>` or
   `<span>` without `tabindex="0"`. Browsers skip them in tab order,
   so `:focus-visible` never fires.
2. The elements are focusable but the ring is invisible against
   Zone 1's pre-existing light-blue header tint.
3. A more specific CSS rule somewhere in the cascade overrides
   `*:focus-visible` for those elements.

**Why closed-premature:** Cannot validate focus rings across multiple
interactive elements when only one zone is rendered. Session 7 Part 3
diagnosis revealed the rendered surface itself was wrong — Zones 2-4
were absent from the DOM, and the "light-blue header tint" of
candidate 2 was actually Zone 1's background filling the viewport.
The candidate-cause analysis presumed an architectural state that did
not hold.

**Re-evaluate when:** Zone 2 component ships under `/analysis` (the
new multi-zone composition point per the 2026-05-13 routing
architecture decision). At that point, focus-ring behaviour can be
validated against multiple interactive elements on a properly
rendered multi-zone layout, and the three candidate causes
re-assessed with the correct architectural baseline.

---

## 2026-05-13 — App entry-point gate (originally IDEA-027)

**Status:** CLOSED-ALREADY-DONE

**Observation:** The dashboard currently has no `python -m mfip.dashboard`
or `python -m mfip` entry-point. Launching the app requires the verbose
`python -c "from mfip.dashboard.app import app; app.run(debug=True, port=8050)"`
incantation, which is fragile to type, easy to misremember between
sessions, and surfaces no validation if the import path drifts.

**Status update 2026-05-13 (Session 8):** `mfip/dashboard/__main__.py`
already exists and works — `python -m mfip.dashboard` launches the
app cleanly (verified during Session 8 step 9 browser verification).
The file was created in an unrecorded step (likely Session 6 or 7);
the IDEA-027 entry in Session 7 Part 3's handoff was based on stale
context. No action required; closing.

**Fix (no longer needed):** Add a minimal `__main__.py` (or equivalent
`__main__` block in `app.py`) so the app can be launched as
`python -m mfip.dashboard`. Approximately 10 minutes of work. No
architectural decision required.

**Provenance:** Originally logged as IDEA-027 on the
`phase1/zone1-focus-diagnosis` branch in Session 7 Part 3. That branch
was abandoned in Session 8 per the 2026-05-13 routing architecture
decision; the item is re-logged here, in the correct file per the
2026-05-13 ideas.md/worklog.md split decision.

---

## 2026-05-13 — CLAUDE.md states repo path only implicitly

**Status:** CLOSED-FIXED

**Closed:** 2026-05-14 — Session 9 close-out tidy-up. Working directory
statement added to `CLAUDE.md`. See `docs: CLAUDE.md state repo working
directory explicitly` commit on main.

**Observation:** `CLAUDE.md` states the repo working directory
(`C:\MFIP\repo\`) only implicitly, via a `← you are here` annotation
on the last entry of the storage tree diagram (line 79). A fresh
Claude Code session reader who doesn't scan the tree first will land
in their home directory and need to ask for the path. This happened
in Session 8 step 2.

**Fix:** Add an explicit "Working directory: `C:\MFIP\repo\`" statement
near the top of `CLAUDE.md`, before the storage layout section.
Trivial edit, ~5 minutes.

**Schedule:** End-of-Phase-1 close-out. Cohesive with the IDEA-027
entry above and the line-endings entry below — all small infra fixes
suited to one tidy-up sub-pass.

---

## 2026-05-13 — Mixed line endings across repo Markdown files

**Status:** CLOSED-FIXED

**Closed:** 2026-05-14 — Session 9 close-out tidy-up. `.gitattributes`
added with `* text=auto eol=lf` to make the LF convention explicit
and repo-local. `git add --renormalize .` produced no staged changes
— `core.autocrlf=true` in global git config had already been storing
all text files as LF in the object database. The original worklog
observation conflated working-tree state (CRLF on Windows checkout)
with repo state (always LF in commits). The `.gitattributes` change
still matters: future clones (e.g. the Mac Mini M4 acquisition in
autumn 2026, or any CI runner) don't depend on the contributor's
global git config. See `decisions.md` 2026-05-14 line-endings learning
entry for the full architectural note.

**Observation:** `decisions.md` uses LF line endings; `ideas.md` uses
CRLF. Surfaced when creating `worklog.md` in Session 8 step 5;
matched `decisions.md` (LF) for the new file. Inconsistency means
future commits to `ideas.md` may produce noisy line-ending diffs
if any editor or git config normalises them. No correctness impact;
purely diff hygiene.

**Fix:** Normalise the repo via `.gitattributes` (`* text=auto eol=lf`)
plus a one-off re-commit pass to apply the normalisation. ~15 minutes.

**Schedule:** End-of-Phase-1 close-out. Third item in the cohesive
small-infra-fixes sub-pass alongside the CLAUDE.md and IDEA-027
entries.

---

## 2026-05-13 — Theme toggle radio updates state but visual result not applied

**Status:** CLOSED-FIXED

**Closed:** 2026-05-14 — `theme.css` created in `assets/`. Root cause was Layer 3 missing entirely: no `[data-theme]` CSS selectors existed, so the color token custom properties were never defined on `html`/`:root` and all `var(--bg-canvas)` etc. resolved to nothing. Layers 1 and 2 (callback chain and `data-theme` attribute write) were already correct. See `fix: theme toggle visual application` commit on main.

**Observation:** After Session 8 routing restructure, `/analysis`
renders Zone 1 correctly and the theme radio (Dark/Light/System)
selects state. However, toggling between options produces no visible
theme change — Home stub and Zone 1 chrome both render as light-mode
(white background, dark text) regardless of which radio is selected.
The page shows a brief "loading" indicator when toggling, suggesting
callbacks fire, but no visual outcome follows.

**Likely cause:** Pre-existing latent issue, not a regression from
the routing restructure. The theme-toggle callback chain (zone1 →
`zone1-theme-radio-store` → `theme-mode-store` → clientside
`data-theme` attribute) was unchanged in Session 8.

**Three diagnostic hypotheses:**
1. Callback chain fires but `data-theme` attribute isn't being set
   on `<html>` — break in JS/Python wiring.
2. `data-theme` attribute IS set but the `[data-theme="..."]` CSS
   rules don't actually exist in the stylesheets — CSS gap.
3. Both A and B — partial wiring on both sides.

**Diagnose by:** DevTools → Elements → inspect `<html>` while
toggling; check whether `data-theme` attribute changes value. If
yes, (B). If no, (A).

**Fix:** Depends on diagnosis. Likely the same effort that picks up
the IDEA-026 focus-ring work when Zone 2 ships, since both are about
Zone 1's chrome-styling completeness.

**Schedule:** With Zone 2 build, or as standalone Zone 1 finishing
pass earlier if Magnus chooses.

---

## 2026-05-13 — "Master dashboard" terminology vs MFIP route tree

**Status:** OPEN

**Observation:** `05_DASHBOARD_SPEC.docx` paragraphs 164-176 describe
a "Master dashboard" hosting the RAG Company Status Grid. After the
2026-05-13 routing decision split `/` (Home stub) and `/analysis`,
"Master dashboard" doesn't map clearly to either route.

**Pre-existing ambiguity surfaced by Session 8's edit pass** but
not resolved by it — the routing decision didn't address what
"Master dashboard" is in relation to MFIP's own route tree.

**Possible interpretations:**
1. Master = the Home stub once built out, showing portfolio overview.
2. Master = a third route distinct from both `/` and `/analysis`.
3. Master = a top-level layout *containing* `/` and `/analysis`.

**Resolution:** Separate design decision needed when RAG grid build
is scoped.

**Schedule:** Phase 7 build-start (when Thesis Monitor ships), or
sooner if a related question forces it.

---

## 2026-05-13 — Backtesting Panel "tab view" framing predates multi-route stance

**Status:** OPEN

**Observation:** `05_DASHBOARD_SPEC.docx` paragraph 177 and
`04_BUILD_SEQUENCE.docx` Phase 1 checklist describe Backtesting as
"tab view" / "tab in the main area". The 2026-05-13 routing decision
listed backtesting as a "plausible distinct route" (v2). The "tab"
framing predates the multi-route stance and may not survive contact
with the v2 build.

**Schedule:** V2 backtesting build (well past Phase 1).

---

## 2026-05-13 — Zone 1 settings-panel needs density-roomy class

**Status:** OPEN

**Observation:** The Roomy density class isn't applied to Zone 1's
settings panel. Found in Session 7 Part 2 (PR #14) but the PR was
closed without merging per the 2026-05-13 routing architecture
decision. The one-line fix lived only on the deleted
`phase1/zone1-density-focus` branch; re-logging here to preserve the
finding when Zone 1 chrome styling is taken on.

**Fix:** Apply `density-roomy` class to the settings panel container
in `mfip/dashboard/zones/zone1.py`. One-line change.

**Schedule:** With Zone 1 chrome styling completeness work (theme
visual application, focus rings, etc. — all in the same family).

---

## 2026-05-14 — Session 13 discovered stale branches from Sessions 7–12
Five branches were left undeleted after their PRs merged across
Sessions 7–12, despite Session 12's handoff stating cleanup
happened: `fix/theme-css-layer3`, `docs/decisions-self-indexing`,
`docs/decisions-theme-css-entry`, `docs/claude-md-decisions-commit-timing`,
`test/idea-023-served-layout-resolution`. All content was already
on `main` via PRs #25, #26, #29, #30 — content loss risk was nil,
but the dirty state caused two pre-flight failures at the start of
Session 13.

**Lesson:** "Cleanup happened" assertions in handoff documents
should be verified, not trusted. Cleanup PR conventions going
forward should explicitly include `git branch -d <branch>` and
`git push origin --delete <branch>` as the closing steps of any
work that merges a feature branch, run in the same session as
the merge.

Cleared in Session 13 via `chore/session-12-cleanup-residue` PR.

---

## 2026-05-14 — Venv missing on Phase 2 PR-A start

**Status:** CLOSED-RECOVERED

`C:\MFIP\repo\.venv\` was found missing at the start of Session 14's
Phase 2 PR-A work. Phase 0 had declared the venv built; `MEMORY.md`
listed it as built; Session 13's handoff assumed it. Cause not
definitively identified — possible candidates include silent
`git clean -fdx`, partial restic restore not including the `.venv`
exclusion, or manual removal.

Python 3.12.10 interpreter was intact (`py -3.12 --version` confirmed).
Recovery was mechanical: `py -3.12 -m venv .venv` +
`pip install -r requirements.lock.txt`. All 25 existing tests green
after recovery; dashboard launches cleanly.

**Defensive note for `MEMORY.md`:** the venv is not Git-tracked
(correctly — venvs never go in repos) and is excluded from restic.
If it goes missing again, the recovery is `py -3.12 -m venv .venv`
followed by `pip install -r requirements.lock.txt`. Consider a
`make venv` or PowerShell convenience script later if this recurs.

---

## 2026-05-14 — 06_SECURITY_COUNCIL.docx schema text needs update

**Status:** OPEN

`06_SECURITY_COUNCIL.docx` AUDIT TRAIL section contains the original
`security_log` schema without `correlation_id`. Superseded by
`decisions.md` 2026-05-14 "security_log schema extension". Design doc
text needs manual update by Magnus in a non-code pass — not blocking,
but worth tracking. Close when the docx file is updated.

---

## 2026-05-15 — `.env` missing despite Phase 0 marked complete

**Status:** CLOSED — `.env` created and verified 2026-05-15 (populated,
gitignored, no BOM, 17 lines, pytest 37/37 green). Phase 0's `.env`
deliverable is now reconciled in fact even if not in checklist text.

**Discovered:** Pre-Session-15B credential setup revealed that
`C:\MFIP\repo\.env` does not exist. A whole-tree `Get-ChildItem`
search for `.env*` across `C:\MFIP\` returned no matches. Phase 0's
completion checklist listed ".env created" as a deliverable; either
it never existed or it was deleted at some point (possibly during the
Session 14 venv recovery, though there's no direct evidence linking
the two).

**Resolved (in-PR portion):** Created `.env.example` as a tracked
template (this PR). Magnus creates the real `.env` manually
post-merge by copying the example and filling in SMTP credentials
generated from his Google Account (Gmail app password, requires
2FA-enabled account). Real `.env` is gitignored (`.gitignore` line 29)
and stays untracked.

**Lesson:** Phase completion checklists should be verified against
filesystem state at close-out, not just trusted as self-reports. For
future phase close-outs, add a "verify all listed deliverables exist
on disk" step before flipping the phase status to ✅.

**Closes when:** Magnus confirms `.env` is populated with real SMTP
credentials and pytest still 37/37 green. Then this entry flips to
`CLOSED-PHASE-0-RECONCILED` and the Phase 0 status line in `MEMORY.md`
gets a footnote acknowledging the post-hoc fix.

**Closed:** 2026-05-15. Magnus completed manual `.env` creation between
Session 15A close-out (PR #41, commit 23085f0) and Session 15B kickoff.
File verified: exists at `C:\MFIP\repo\.env`, gitignored via
`.gitignore` line 29, contains all five `MFIP_SMTP_*` keys, UTF-8
without BOM, 17 lines. SMTP delivery itself is exercised in PR-B
(`mfip_alerts.py`) — if SMTP fails, that opens a new worklog entry,
not a reopening of this one.

---

## 2026-05-15 — Severity casing inconsistency: Alert.severity (Title) vs SecurityLogEntry.severity (UPPER)

**Status:** OPEN — flagged for normalisation; not blocking PR-B or PR-C.

**Discovered:** PR-B (`mfip_alerts.py`, PR #43) needed to write delivery-status rows to `security_log` from an `Alert` model. The two models use different severity casing conventions:
- `Alert.severity: Literal["Critical", "Warning", "Advisory"]` — Title case.
- `SecurityLogEntry.severity: Literal["CRITICAL", "WARNING", "ADVISORY"]` — UPPER case.

PR-B resolved this at the sender boundary via a private `_ALERT_TO_LOG_SEVERITY` mapping. Neither model was modified. The mismatch is invisible inside the alerts module but will resurface every time another agent writes to `security_log`.

**Impact:** Every future agent that writes to `security_log` either has to import the mapping from `mfip/alerts/sender.py` (creating an unwanted dependency from agent code onto the alerts module) or has to redefine the same mapping locally (duplicated convention). Neither is good.

**Proposed resolution:** Normalise both models to one convention. Either:
- Option A: Change `SecurityLogEntry.severity` to Title-case. Updates to PR-A's existing tests, PR-B's mapping removed.
- Option B: Change `Alert.severity` to UPPER. Cosmetic change to user-facing alert HTML (the severity label appears in the header bar).

Option A is preferred — Title-case reads more naturally in human-facing contexts (alert emails, logs scanned by Magnus), and "log severity" is a fundamentally human-readable field.

**Closes when:** Both models use the same severity casing and PR-B's `_ALERT_TO_LOG_SEVERITY` mapping is removed. Not blocking — defer to a small dedicated PR before Phase 3 starts (when more agents begin writing to `security_log`). Estimated 30 minutes including test updates.

**Closed:** 2026-05-15 (Session 16 Item B). Resolved via Option A:
`SecurityLogEntry.severity` changed to Title-case to match
`Alert.severity`. `_ALERT_TO_LOG_SEVERITY` mapping in
`mfip/alerts/sender.py` removed. Production DB rows migrated
in-place using the new `--migrate` flag in `scripts/init_db.py`.
All three existing `ADVISORY` rows preserved as `Advisory`.
Status is now CLOSED.

---

## 2026-05-15 — correlation_id silent fallback in mfip_alerts (fixed in PR-B follow-up bundle)

**Status:** CLOSED — fixed in this PR.

**Discovered:** PR-B's deviation review flagged that `mfip/alerts/sender.py` was silently coercing malformed `correlation_id` strings to `None` when constructing the delivery-status `SecurityLogEntry`. The reasoning at PR-B time was "defensive against a broken caller," but the side effect was that a real upstream bug (a caller passing a non-UUID string) would be invisible in the audit trail.

**Resolution (this PR):** When `UUID(alert.correlation_id)` raises, the alert layer now:
1. Sets `log_correlation_id = None` for the delivery-status row (preserving non-blocking alert delivery — correct behaviour).
2. Additionally writes a separate Warning `SecurityLogEntry` flagging the malformed input, with the raw input value captured in `impact_assessment` JSON for upstream debugging.
3. Continues with the SMTP send as before.

The warning write is wrapped in try/except — if it fails, the alert delivery is not blocked. The alert layer's contract is "deliver and report status"; anomaly flagging is best-effort.

**Test coverage:** `tests/alerts/test_sender.py::test_malformed_correlation_id_writes_warning_and_proceeds` exercises the path. Verifies delivery succeeds, both rows are written, and the raw input is captured in the warning's `impact_assessment`.

---

## 2026-05-15 — Schema not initialised on production DB despite PR-A marked complete

**Status:** CLOSED — fixed in this PR. Recurring pattern flagged for future phase close-outs.

**Discovered:** Session 15B's live alert test crashed with `Catalog Error: Table with name security_log does not exist`. Investigation showed `C:\MFIP\runtime\mfip.duckdb` existed (12 KB, created during the live test itself by DuckDB's auto-create-on-connect) but contained zero application tables. PR-A (Session 14) shipped `scripts/init_db.py` to create the schema, but the script had never been run against the production DB. Tests passed because they use temporary DBs that get the schema fresh each time; production had never been touched.

**Pattern:** This is the second instance in two sessions of a "phase deliverable marked complete because the code that produces the artifact shipped, but the artifact itself was never created" pattern. First was Session 15A's `.env` discovery (file missing despite Phase 0 marked complete). Same structural defect.

**Lesson (broader than this PR):** Phase completion checklists should verify deliverable artifacts exist on disk and behave as expected, not just verify that the code producing them was merged. For future phase close-outs, the close-out checklist should include a "run the bootstrap" step that exercises each runtime artifact end-to-end:

- `.venv` exists and `pip list` shows the lockfile contents → already covered by Session 14's venv recovery recipe
- `.env` exists and has all expected keys → covered by the `.env.example` introduced in Session 15A
- DB exists and has expected tables → fixed in this PR by making `init_db.py` idempotent and adding it to README first-time-setup
- Any other phase-specific artifacts (Bloomberg templates archived, dashboard launches cleanly, etc.) → check each at phase close-out, not just at code-merge

The README "First-time setup" section introduced in this PR is the operational counterpart to the lesson — by listing all bootstrap steps in one place, any future fresh-clone scenario (including a future Claude Code session on a different machine) follows the same recipe.

**Resolution (this PR):**

1. Made `scripts/init_db.py` idempotent with schema verification (three cases: empty → apply, current → no-op, drift → exit 1 with diff). EXPECTED_SCHEMA dict is the source of truth for what the verifier checks against; update it any time `mfip/logging/schema.sql` changes.
2. Ran the script against production DB; schema now applied (`decision_log` + `security_log` tables present). The "file exists but empty" state from the failed live test was handled by the same code path as "file doesn't exist" — DuckDB creates tables in either case once `init_db.py` runs.
3. Added "First-time setup" section to README listing all five bootstrap steps in order.
4. This worklog entry documents the recurring pattern so the lesson doesn't get lost.

**Test coverage:** The script's three cases (empty, current, drift) were exercised manually in this PR using a temp DB with simulated drift (an unexpected extra column). Adding automated tests for the script itself is out of scope — it's a one-shot operational tool, not pipeline code. If schema drift becomes a frequent concern (it shouldn't until Phase 3+), revisit and add tests then.

**Verify after this PR:** Live alert test from Session 15B can now complete end-to-end. SMTP + render + `security_log` write all succeed. Closing condition for the prior `worklog.md` entries (`.env missing` and the original Phase 2 PR-A claim of "schema created") is now genuinely met.

---

## 2026-05-15 — Outlook quarantine of MFIP alert mail (resolved by service-account redesign)

**Status:** CLOSED — resolved by switching to Gmail-to-Gmail delivery via service-account separation. See `decisions.md` 2026-05-15 entry on service-account separation.

**Discovered:** Session 15B's live alert test (PR-B validation) confirmed SMTP send succeeded and `security_log` row was written correctly, but the alert email did not arrive at `magnus.t@live.no` (Outlook). Manual emails between the same accounts initially also failed; mutual contact-add resolved some but not all delivery. Forwarding the email manually from Gmail in the same thread DID arrive at Outlook, proving the content was not being rejected — the sender-recipient pair was being filtered by Microsoft's anti-spam classifier.

**Investigation summary:** Live runs of `live_alert_test.py` (correlation IDs `8b4c3eea-cc8c-4c52-950e-24329540e539`, `0e3dd879-4d8e-4481-ad9b-a6278f49e765`, `0809d4b7-f68e-475e-acc9-2ca37449bae0`) confirmed the SMTP and rendering paths work; the `security_log` write worked after PR #45 fixed the schema bootstrap. A CC-routing diagnostic (`live_alert_test_cc.py`, correlation ID `65843789-e0a3-4b8c-9e64-d74d332f0635`) routed primary delivery to a Gmail recipient with Outlook on CC; the Gmail leg succeeded but the Outlook leg outcome was inconclusive enough that continuing iteration would have been speculative.

**Resolution (this PR):** MFIP alert delivery configuration switched per `decisions.md` 2026-05-15 service-account separation entry. Outlook is no longer in the alert path. The Outlook quarantine pattern itself remains documented as a parking-lot item in `ideas.md` (IDEA-029).

**Closing note:** All MFIP alerts module behaviour (SMTP, render, `security_log` write, drain queue) is validated working end-to-end. The Outlook-delivery question turned out to be a recipient-platform problem, not an MFIP problem.

---

## 2026-05-15 — IDEA-028 duplicate in `ideas.md` cleaned up + tie-breaker rule adopted

**Status:** CLOSED

Two `IDEA-028` entries existed in `ideas.md`, both added 2026-05-14:
"Claude Code context management playbook" (appears earlier in the
file) and "Chief Analyst discovery form pattern" (appears later).
The collision was flagged in Session 15B PR #46's report-back and
cleared in Session 16 Item A.

**Resolution:** The later entry — "Claude Code context management
playbook" — was renumbered to `IDEA-030`. `IDEA-029` was taken in
PR #46 for the Outlook delivery investigation.

**Tie-breaker rule adopted for future duplicate-ID resolution.**
Applied in this order:

1. **Cross-reference check (primary).** If one duplicate is
   referenced from elsewhere in the repo, that one keeps the
   original number and the un-referenced one is renumbered.
   Cross-references would dangle if the referenced entry's number
   changed; renumbering the un-referenced entry costs nothing.
2. **File position (fallback).** If neither (or both) duplicates
   are referenced externally, the entry appearing earlier in the
   file keeps the number. The author who wrote the second entry
   would have caught the collision at write time if file order had
   been swapped.
3. **Commit-order verification (defensive).** Confirm file-position
   matches commit-introduction order before executing the renumber.
   If they disagree, halt and re-evaluate.

The rule applies to any ID-bearing file in the repo — `ideas.md`,
`worklog.md`, and future equivalents.

**Application to this case:** `git grep -n "IDEA-028"` returned hits
only inside `ideas.md`. The cross-reference gate did not fire. File
position was applied as the fallback. Commit-order matched file
position (verified at execution time). The Claude Code context
management playbook entry — file-position-later (line 1535),
commit-order-later — was the renumbering target. The Chief Analyst
discovery form pattern entry (line 1064, file-position-earlier,
commit-order-earlier) keeps `IDEA-028`.

---

## 2026-05-15 — Migrations module refactor trigger flagged

**Status:** OPEN

Session 16 Item B added `--migrate` to `scripts/init_db.py` with the
row transform for the severity-casing migration encoded as a single
named function (`_transform_row_severity_to_title_case`) registered
via module-level constant `ROW_TRANSFORM`. This shape is correct
for v1's needs but does not scale.

**Refactor trigger:** When migration #2 lands (any future schema
change requiring its own row transform), refactor at that point
into a dedicated `mfip/logging/migrations/` module — one file per
migration, each exporting a `transform(row, table_name)` function
and a `description` string. The runner in `init_db.py` then
discovers migrations in order rather than referencing a single
constant.

**Why wait:** Building the abstraction now from one example
produces a guess. Building it from two concrete cases produces a
fit. The cost of the refactor at #2 is small (the one existing
transform moves into a file; the runner picks it up from there).

**Closes when:** Either the migrations module gets built, or the
project ships v1 with only this one migration in its history (no
further trigger reached).

---

## 2026-05-15 — Phase 1 gap: Zone 2-4 placeholder containers shipped without layout or visible content

**Status:** CLOSED — fixed in this PR.

**Discovered:** Session 16's live validation walkthrough (Item C)
revealed that `/analysis` rendered Zone 1 at the top with a vast
empty canvas below. Initial diagnosis suspected DOM-absence; closer
inspection during the handoff discovery phase showed the
placeholders are in fact present as inert `html.Div` containers
with IDs `zone-2`, `zone-3`, `zone-4` and class `zone-placeholder`.
What's missing is everything that would make them visible: no CSS
file targets any of those IDs (`grep` across the five existing
`assets/*.css` files returns zero matches); the divs are
content-empty; no grid layout positions them. The containers
exist structurally and render to zero visible pixels.

**Pattern this fits.** Different shape from the two prior instances
in the current arc:
- First instance (`.env` missing, PR #41): true artifact absence —
  the file did not exist on disk.
- Second instance (DuckDB schema not initialised, PR #45): true
  artifact absence — the tables did not exist in the database.
- This instance (Zone 2-4 visibility): the artifact exists at the
  structural level (DOM containers with stable IDs are mounted)
  but not at the level Phase 1's principle required ("dashboard
  must look complete and professional in both dark and light mode
  with placeholder data"). Empty unstyled divs fail that standard.

The underlying defect is the same — phase close-out passed on
self-report rather than visible-walkthrough confirmation — but the
artifact-vs-visibility distinction matters for diagnosis. A
filesystem walk would not have caught this; only a browser
walkthrough does. The `phase-validations/` pattern (Item 0) covers
both: its "Runtime artifacts verified on disk" section handles the
first two cases, and its "Live exercise log" section handles this
third one.

**Resolution (this PR):** Added CSS grid layout for the existing
`zone-2`/`zone-3`/`zone-4` placeholder containers in a new file
`mfip/dashboard/assets/analysis-layout.css`. Layout per
`05_DASHBOARD_SPEC.docx` LAYOUT STRUCTURE: 60/40 horizontal split
between Zones 2 and 3, 65/35 vertical split between Zones 2+3 and
Zone 4, 8px gap. Added title/caption children to each placeholder
so they show "Zone N — <Name>" and "Phase 1 placeholder" captions.
Border uses `--border-subtle` to read as inert chrome. Container
IDs unchanged (`zone-2`, `zone-3`, `zone-4`) so the same IDs carry
through to when each zone's real components ship — no rename
needed in Phase 5+ or Phase 8.

**Future placeholders:** Zone-internal design decisions remain
deferred per existing `ideas.md` decision gates:
- Zone 2 design pass: run-up to Phase 5 (Intelligence Layer kickoff)
- Zone 3 design pass: same as Zone 2
- Zone 4 design pass: before Phase 8 (per `2026-05-10 — Portfolio
  overview` entry)

The placeholder containers ship here as visible cards with labels;
each gets internal content (cards, charts, tables) at the
respective zone's design-pass moment.
