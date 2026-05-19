"""Bloomberg workbook parser — public entrypoint.

The canonical API is:

    parse_workbook(path: Path, *, validation_policy=ValidationPolicy.STRICT) -> ParsedCompanyData

The parser is a pure function: it does not write to decision_log,
does not send alerts, does not modify the input file. It emits
stdlib `logging` calls at INFO/WARNING/ERROR; callers route them.

Per-sheet extraction is delegated to private helpers; PR #62b ships
the wiring with CONFIG live and other sheets stubbed. PRs #63-#65
fill in the sheet-extraction bodies.
"""

import argparse
import logging
import sys
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path

from openpyxl import load_workbook

from mfip.ingestion.bloomberg.exceptions import (
    BloombergParserError,
    WorkbookExtractionError,
    WorkbookValidationError,
)
from mfip.ingestion.bloomberg.models import (
    AnalystRecommendationsSheet,
    BetaSheet,
    DividendSheet,
    EarningsEstimatesSheet,
    ParsedCompanyData,
    ParsedFXData,
    ParsedIndicesData,
    PriceHistorySheet,
    RVCompsSheet,
)
from mfip.ingestion.bloomberg.validator import (
    FILENAME_RE,
    Tier,
    validate_workbook,
)

logger = logging.getLogger(__name__)


class ValidationPolicy(Enum):
    """Controls parser behaviour when the validator returns a FAIL.

    STRICT (default): FAIL raises WorkbookValidationError. ADVISORY
        logged and carried forward into ParsedCompanyData.advisories.
        PASS proceeds silently. The v2-watchdog-friendly default.

    PERMISSIVE: FAIL logged as WARNING, parser attempts extraction
        anyway. For development / debugging only. Not used by agents.

    (REPORT_ONLY was specified in the original design doc but dropped
    in PR #62b — it duplicated PERMISSIVE's behaviour with no
    additional capability. Reintroduce when a consumer demonstrably
    needs it.)
    """

    STRICT = "strict"
    PERMISSIVE = "permissive"


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def parse_workbook(
    path: Path,
    *,
    validation_policy: ValidationPolicy = ValidationPolicy.STRICT,
) -> ParsedCompanyData:
    """Parse a Bloomberg company workbook into ParsedCompanyData.

    Per-sheet extraction is stubbed in PR #62b — every sub-model
    returns its default-empty form. CONFIG extraction (ticker,
    currency) is functional. validation_report and advisories are
    populated.

    Args:
        path: Path to the .xlsx workbook.
        validation_policy: How to handle a validator FAIL result.

    Returns:
        ParsedCompanyData with provenance, CONFIG fields, and
        validation_report populated; all per-sheet sub-models
        empty pending #63 onward.

    Raises:
        WorkbookValidationError: validator returned FAIL and policy
            is STRICT. NB: this catches the nonexistent-path case too
            (validator reports FILE_NOT_FOUND).
        WorkbookExtractionError: validator passed but openpyxl could
            not open the file, or CONFIG cells are malformed.
    """
    logger.info("Parsing workbook: %s", path)

    # 1. Validate first. The parser trusts the validator's contract
    #    check; it does not re-validate sheet presence or RV column
    #    shapes itself.
    report = validate_workbook(path)
    advisories = [f for f in report.findings if f.tier == Tier.ADVISORY]

    if report.tier == Tier.FAIL:
        if validation_policy == ValidationPolicy.STRICT:
            raise WorkbookValidationError(report)
        else:  # PERMISSIVE
            logger.warning(
                "Validator FAIL but PERMISSIVE policy — proceeding (%d findings)",
                len(report.findings),
            )
    elif report.tier == Tier.ADVISORY:
        logger.info("Validator ADVISORY: %d findings", len(advisories))

    # 2. Open the workbook. data_only=True reads cached values
    #    (paste-as-values output); read_only=True is faster.
    try:
        wb = load_workbook(path, data_only=True, read_only=True)
    except Exception as exc:
        raise WorkbookExtractionError("(workbook open)", str(exc)) from exc

    try:
        # 3. Extract CONFIG (ticker + currency). Other sheets are
        #    stubbed — they return default-empty sub-models pending
        #    PR #63 onward.
        ticker, ticker_short, config_currency = _extract_config(wb, path)

        result = ParsedCompanyData(
            source_path=path,
            parsed_at=datetime.now(timezone.utc),
            validation_report=report,
            advisories=advisories,
            ticker=ticker,
            ticker_short=ticker_short,
            config_currency=config_currency,
            listing_currency="",   # populated in PR #65
            is_gbp_pence=False,    # populated in PR #65
            beta=_extract_beta(wb),
            dvd=_extract_dvd(wb),
            ee=_extract_ee(wb),
            anr=_extract_anr(wb),
            hp_monthly=_extract_hp_monthly(wb),
            hp_daily=_extract_hp_daily(wb),
            rv_comps=_extract_rv_comps(wb),
        )
    finally:
        wb.close()

    logger.info("Parsed: ticker=%s advisories=%d", ticker_short, len(advisories))
    return result


def parse_indices_workbook(path: Path) -> ParsedIndicesData:
    """Parse the Bloomberg Indices workbook (4 index series).

    Skeleton in PR #62b — returns empty ParsedIndicesData. Full
    extraction lands in PR #66 (which will also add a
    validation_policy parameter once indices validation lands).
    """
    logger.info("Parsing indices workbook: %s", path)
    return ParsedIndicesData(
        source_path=path,
        parsed_at=datetime.now(timezone.utc),
    )


def parse_fx_workbook(path: Path) -> ParsedFXData:
    """Parse the Bloomberg FX workbook (3 FX cross series).

    Skeleton in PR #62b — returns empty ParsedFXData. Full extraction
    lands in PR #66 (which will also add a validation_policy parameter
    once FX validation lands).
    """
    logger.info("Parsing FX workbook: %s", path)
    return ParsedFXData(
        source_path=path,
        parsed_at=datetime.now(timezone.utc),
    )


# ---------------------------------------------------------------------------
# Private extraction helpers (CONFIG functional; others stubbed)
# ---------------------------------------------------------------------------

def _extract_config(wb, path: Path) -> tuple[str, str, str]:
    """Read CONFIG!B3 (ticker) and CONFIG!B4 (currency).

    Returns (ticker, ticker_short, config_currency).
    ticker_short prefers the filename prefix (validator's canonical
    contract via FILENAME_RE), falling back to ticker-string token
    splitting if the filename doesn't match the saved-file naming
    convention.
    """
    try:
        config = wb["CONFIG"]
    except KeyError as exc:
        raise WorkbookExtractionError("CONFIG", "sheet missing") from exc

    ticker = config["B3"].value
    currency = config["B4"].value

    if not isinstance(ticker, str) or not ticker.strip():
        raise WorkbookExtractionError(
            "CONFIG",
            f"B3 (ticker) malformed: {ticker!r}",
        )

    ticker_short = _derive_ticker_short(path, ticker)

    # Currency may be None / empty on the template (master workbook
    # before lab fill-in) or non-USD on a saved file (validator surfaces
    # this as ADVISORY, not FAIL — parser must not promote).
    config_currency = currency.strip() if isinstance(currency, str) else ""

    return ticker, ticker_short, config_currency


def _derive_ticker_short(path: Path, ticker_str: str) -> str:
    """Derive ticker_short. Filename is authoritative; ticker is fallback.

    The validator's FILENAME_RE matches the saved-file naming convention
    (e.g. "EQNR_NO_2026-05-08.xlsx") and exposes the prefix as a named
    group. When the filename matches, use that — it's the contract.

    Falls back to splitting the ticker string on whitespace and joining
    the first two tokens with underscore — works for the v1 universe
    but is cosmetically dependent on Bloomberg's ticker conventions.
    """
    match = FILENAME_RE.match(path.name)
    if match:
        return match.group("prefix")

    tokens = ticker_str.strip().split()
    if len(tokens) >= 2:
        return f"{tokens[0]}_{tokens[1]}"

    raise WorkbookExtractionError(
        "CONFIG",
        f"cannot derive ticker_short from filename={path.name!r} "
        f"or ticker={ticker_str!r}",
    )


def _extract_beta(wb) -> BetaSheet:
    """STUB — populated in PR #63."""
    return BetaSheet()


def _extract_dvd(wb) -> DividendSheet:
    """STUB — populated in PR #64."""
    return DividendSheet()


def _extract_ee(wb) -> EarningsEstimatesSheet:
    """STUB — populated in PR #63."""
    return EarningsEstimatesSheet()


def _extract_anr(wb) -> AnalystRecommendationsSheet:
    """STUB — populated in PR #65."""
    return AnalystRecommendationsSheet()


def _extract_hp_monthly(wb) -> PriceHistorySheet:
    """STUB — populated in PR #64."""
    return PriceHistorySheet()


def _extract_hp_daily(wb) -> PriceHistorySheet:
    """STUB — populated in PR #64."""
    return PriceHistorySheet()


def _extract_rv_comps(wb) -> RVCompsSheet | None:
    """STUB — populated in PR #65.

    Returns None when sheet absent (pre-lab Master template path).
    Returns empty RVCompsSheet when sheet present but extraction
    not yet wired.
    """
    if "RV_Comps" not in wb.sheetnames:
        return None
    return RVCompsSheet()


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> int:
    """Thin CLI shell. Usage: python -m mfip.ingestion.bloomberg.parser <path>"""
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("path", type=Path, help="Path to Bloomberg workbook")
    cli.add_argument(
        "--policy",
        choices=[p.value for p in ValidationPolicy],
        default=ValidationPolicy.STRICT.value,
        help="Validation policy (default: strict)",
    )
    args = cli.parse_args()

    policy = ValidationPolicy(args.policy)
    try:
        result = parse_workbook(args.path, validation_policy=policy)
    except WorkbookValidationError as exc:
        print("FAIL: validation refused", file=sys.stderr)
        print(exc.report.render(), file=sys.stderr)
        return 1
    except BloombergParserError as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1

    print(f"PARSED: {result.ticker_short}")
    print(f"  Validation: {result.validation_report.tier.value}")
    print(f"  Advisories: {len(result.advisories)}")
    print(f"  Source: {result.source_path}")
    return 0


if __name__ == "__main__":
    # Configure root logger only when invoked from CLI — never when
    # parse_workbook is called programmatically from another module.
    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s %(name)s: %(message)s",
    )
    sys.exit(main())
