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
