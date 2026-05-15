# Phase N Validation

**Phase:** [name]
**Status:** [In progress / Complete]
**Started:** [YYYY-MM-DD]
**Completed:** [YYYY-MM-DD or "N/A"]
**Validated by:** Magnus Thomassen
**Session:** [session number]

---

## Phase deliverables checklist

Every item from this phase's entry in `04_BUILD_SEQUENCE.docx`, each
with a checkbox and an `evidence:` sub-line linking to the PR,
commit, or artifact that delivered it.

- [ ] Deliverable 1
  - evidence: [PR #N / commit SHA / artifact path]
- [ ] Deliverable 2
  - evidence: [PR #N / commit SHA / artifact path]

---

## Runtime artifacts verified on disk

Every runtime artifact this phase was supposed to produce — `.env`,
DB files, output directories, scheduled tasks, etc. Each artifact
gets two checkboxes: existence and behaviour.

- [ ] Artifact 1 (e.g. `C:\MFIP\repo\.env`)
  - [ ] verified existing
  - [ ] verified behaving correctly
  - notes: [how verified, what was checked]

---

## Live exercise log

What was actually clicked, run, or invoked during validation. Be
specific about commands and what the observed output was. This
section is the audit trail proving the phase was exercised, not
just self-reported.

- [date, action, observed result]
- [date, action, observed result]

---

## Findings

### Working as intended

- [list of features/artifacts that behaved correctly]

### Issues discovered (fixed in this session)

- [issue] — fixed in [PR #N / commit SHA]

### Issues discovered (fixed in later sessions)

- [issue] — fixed in [PR #N / commit SHA] (Session [N])

### Issues discovered (deferred)

- [issue] — tracked in [`worklog.md` YYYY-MM-DD entry / `ideas.md`
  IDEA-NNN]

---

## Sign-off

- [ ] I have personally walked through every deliverable and runtime
  artifact above and confirmed each one.

**Signed:** Magnus Thomassen
**Date:** [YYYY-MM-DD]
