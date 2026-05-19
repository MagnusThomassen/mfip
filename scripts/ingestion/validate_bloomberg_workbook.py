"""Thin CLI shell — delegates to mfip.ingestion.bloomberg.validator.

The validator logic moved to mfip/ingestion/bloomberg/validator.py in
PR #62a. This shell preserves the existing invocation:

    python scripts\\ingestion\\validate_bloomberg_workbook.py --all
    python scripts\\ingestion\\validate_bloomberg_workbook.py --file <path>

Both forms behave identically to the canonical:

    python -m mfip.ingestion.bloomberg.validator --all
"""

from __future__ import annotations

import sys
from pathlib import Path

# Imports from mfip.* — script needs sys.path manipulation since this
# file is invoked as `python scripts/ingestion/...` rather than as a
# module. Mirrors scripts/scheduled_tasks/nightly_log_export.py.
_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from mfip.ingestion.bloomberg.validator import main  # noqa: E402

if __name__ == "__main__":
    sys.exit(main())
