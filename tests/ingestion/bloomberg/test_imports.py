"""Sanity tests for the mfip.ingestion.bloomberg public surface.

Confirms the PR #62a move + extraction left the public API
importable. Functional tests against real workbooks come in
PR #62b (parser scaffolding) and downstream Phase 3 PRs.
"""

from __future__ import annotations


def test_validator_public_surface_importable():
    """The names the parser will depend on must import from validator."""
    from mfip.ingestion.bloomberg.validator import (
        DATA_SHEETS,
        EXPECTED_CONFIG_CURRENCY,
        Finding,
        REQUIRED_SHEETS,
        RV_BASELINE_COLUMNS,
        RV_PLANNED_COLUMNS,
        Tier,
        ValidationReport,
        main,
        validate_workbook,
    )
    assert callable(validate_workbook)
    assert callable(main)
    assert Tier.PASS.name == "PASS"
    assert Tier.ADVISORY.name == "ADVISORY"
    assert Tier.FAIL.name == "FAIL"
    assert "RV_Comps" in REQUIRED_SHEETS
    assert "CONFIG" in REQUIRED_SHEETS
    assert "CONFIG" not in DATA_SHEETS
    assert EXPECTED_CONFIG_CURRENCY == "USD"
    # Finding is a dataclass; sanity-check it constructs.
    f = Finding(Tier.PASS, "X", "y")
    assert f.tier is Tier.PASS
    # ValidationReport sanity-check.
    from pathlib import Path
    r = ValidationReport(file=Path("x"))
    assert r.tier is Tier.PASS  # empty report = PASS
    assert "P/E" in RV_BASELINE_COLUMNS
    assert "EV/EBITDA" in RV_PLANNED_COLUMNS


def test_archive_lookup_public_surface_importable():
    """find_latest_workbook + find_all_latest live in archive_lookup."""
    from mfip.ingestion.bloomberg.archive_lookup import (
        KNOWN_ABSENT,
        UNIVERSE,
        find_all_latest,
        find_latest_workbook,
    )
    assert callable(find_latest_workbook)
    assert callable(find_all_latest)
    assert "EQNR_NO" in UNIVERSE
    assert "TEL_NO" in KNOWN_ABSENT


def test_validator_reimports_archive_constants():
    """validator.py imports UNIVERSE and KNOWN_ABSENT from archive_lookup.

    Guards against the constants getting duplicated and drifting.
    """
    from mfip.ingestion.bloomberg import archive_lookup, validator
    assert validator.UNIVERSE is archive_lookup.UNIVERSE
    assert validator.KNOWN_ABSENT is archive_lookup.KNOWN_ABSENT
