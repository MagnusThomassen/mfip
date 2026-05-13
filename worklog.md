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

**Status:** OPEN

**Observation:** The dashboard currently has no `python -m mfip.dashboard`
or `python -m mfip` entry-point. Launching the app requires the verbose
`python -c "from mfip.dashboard.app import app; app.run(debug=True, port=8050)"`
incantation, which is fragile to type, easy to misremember between
sessions, and surfaces no validation if the import path drifts.

**Fix:** Add a minimal `__main__.py` (or equivalent `__main__` block in
`app.py`) so the app can be launched as `python -m mfip.dashboard`.
Approximately 10 minutes of work. No architectural decision required.

**Provenance:** Originally logged as IDEA-027 on the
`phase1/zone1-focus-diagnosis` branch in Session 7 Part 3. That branch
was abandoned in Session 8 per the 2026-05-13 routing architecture
decision; the item is re-logged here, in the correct file per the
2026-05-13 ideas.md/worklog.md split decision.

**Schedule:** End-of-Phase-1 close-out. Bundle with other small infra
fixes if any accumulate by then.

---

## 2026-05-13 — CLAUDE.md states repo path only implicitly

**Status:** OPEN

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

**Status:** OPEN

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
