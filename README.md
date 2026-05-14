# logs-archive

Orphan branch holding nightly exports of MFIP decision and
security logs. Not a code branch — do not merge to or from `main`.

## What lives here

- `exports/<YYYY-MM-DD>.json` — nightly export of new
  `decision_log` and `security_log` entries since the previous
  export.

## How it gets populated

Windows Task Scheduler runs a Python script nightly at 02:00.
The script:

1. Queries DuckDB for `decision_log` and `security_log` entries
   newer than the most recent file in `exports/`.
2. Writes them to `exports/<today>.json`.
3. Commits and pushes to this branch.

Script source lives on `main` at
`scripts/scheduled_tasks/nightly_log_export.py`.

## Rules

- **Append-only in spirit.** Files here should never be edited
  or deleted manually. If a correction is needed, add a new
  dated file with the correction rather than rewriting history.
- **No code.** This branch is for exported log data only.
- **No merging with `main`.** The branches are deliberately
  disconnected.
