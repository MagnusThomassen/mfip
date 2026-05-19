"""Archive-shape constants and walking helpers for bloomberg_archive\\.

Extracted from validator.py in PR #62a. The split is policy/mechanism:

- This module is the mechanism. It defines what the v1 universe is
  (UNIVERSE), records which members are known-absent today
  (KNOWN_ABSENT), and provides the `find_latest_workbook` and
  `find_all_latest` walkers. The walkers are policy-free — they do
  not interpret KNOWN_ABSENT or decide what an absent folder *means*.

- validator.py is the policy. `validate_all` reads the walker output,
  re-stats absent folders to disambiguate folder-missing from
  no-dated-export, cross-references KNOWN_ABSENT, and chooses
  ADVISORY vs FAIL tiers accordingly.

The Phase 3 parser (PR #62b onward) imports from this module and
applies its own policy as needed.
"""

from __future__ import annotations

import re
from pathlib import Path


# ---------------------------------------------------------------------------
# Universe + archive-shape constants
# ---------------------------------------------------------------------------

UNIVERSE: set[str] = {
    "EQNR_NO", "DNB_NO", "TEL_NO", "NOVOB_DC", "MSFT_US", "CKN_LN",
}

# Tickers we know are not present in the 2026-05-08 archive yet. Surfacing
# this as a known-absent rather than a hard fail keeps --all useful while
# the lab catches up. Callers decide the tier; this module just records
# the set.
KNOWN_ABSENT: set[str] = {"TEL_NO"}

DATE_FOLDER_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


# ---------------------------------------------------------------------------
# Walkers
# ---------------------------------------------------------------------------

def find_latest_workbook(company_dir: Path) -> Path | None:
    """Pick the latest YYYY-MM-DD subfolder under a company folder.

    Returns the .xlsx inside, or None if no valid date folders / no .xlsx.
    """
    if not company_dir.is_dir():
        return None
    date_dirs = [
        d for d in company_dir.iterdir()
        if d.is_dir() and DATE_FOLDER_RE.match(d.name)
    ]
    if not date_dirs:
        return None
    latest = max(date_dirs, key=lambda d: d.name)
    xlsx_files = list(latest.glob("*.xlsx"))
    if not xlsx_files:
        return None
    if len(xlsx_files) > 1:
        # Surface this in the per-file report rather than silently pick one.
        # We'll return the lexicographically first; the report will note it.
        return sorted(xlsx_files)[0]
    return xlsx_files[0]


def find_all_latest(archive_root: Path) -> dict[str, Path | None]:
    """Walk archive_root, return {company_prefix: latest_workbook_path | None}.

    None means "no workbook resolvable" — either the company folder doesn't
    exist on disk, or it exists but contains no <DATE>/*.xlsx. Callers
    distinguish by re-statting archive_root / prefix.

    UNIVERSE membership defines the keys; KNOWN_ABSENT is NOT consulted
    here — known-absent treatment is a caller-side policy. validate_all()
    in validator.py handles the three-way disambiguation (folder-missing
    + known-absent → ADVISORY, folder-missing + unknown → FAIL,
    folder-present + no dated export → FAIL).
    """
    results: dict[str, Path | None] = {}
    for prefix in UNIVERSE:
        company_dir = archive_root / prefix
        results[prefix] = find_latest_workbook(company_dir)
    return results
