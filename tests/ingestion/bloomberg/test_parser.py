"""Parser scaffolding tests.

Functional per-sheet extraction tests come in PR #63 onward; this
file covers the scaffolding: public API surface, model construction,
validator integration seam, exception hierarchy, CLI smoke.
"""

from datetime import datetime, timezone
from pathlib import Path

import openpyxl
import pytest

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
    PriceHistorySheet,
    RVCompsSheet,
)
from mfip.ingestion.bloomberg.parser import (
    _NA_VALUES,
    _extract_beta,
    _extract_ee,
    _read_scalar,
    ValidationPolicy,
    parse_fx_workbook,
    parse_indices_workbook,
    parse_workbook,
)
from mfip.ingestion.bloomberg.validator import ValidationReport

REPO_ROOT = Path(__file__).resolve().parents[3]
TEMPLATES = REPO_ROOT / "templates" / "bloomberg"
MASTER_TEMPLATE = TEMPLATES / "Template_Ticker" / "MFIP_Bloomberg_Export_Template_Master.xlsx"
INDICES_TEMPLATE = TEMPLATES / "Template_Index" / "MFIP_Bloomberg_Export_Template_Indices.xlsx"
FX_TEMPLATE = TEMPLATES / "Template_FX" / "MFIP_Bloomberg_Export_Template_FX.xlsx"

FIXTURES = Path(__file__).resolve().parent.parent.parent / "fixtures" / "bloomberg"
EQNR_FIXTURE = FIXTURES / "EQNR_NO_2026-05-08.xlsx"


# ---------------------------------------------------------------------------
# Public surface importability
# ---------------------------------------------------------------------------

class TestPublicSurface:
    def test_parser_module_exports(self):
        """The public names are importable and have expected shapes."""
        assert callable(parse_workbook)
        assert callable(parse_indices_workbook)
        assert callable(parse_fx_workbook)
        assert ValidationPolicy.STRICT.value == "strict"
        assert ValidationPolicy.PERMISSIVE.value == "permissive"
        # REPORT_ONLY intentionally dropped — verify it's not there
        assert not hasattr(ValidationPolicy, "REPORT_ONLY")

    def test_exception_hierarchy(self):
        assert issubclass(WorkbookValidationError, BloombergParserError)
        assert issubclass(WorkbookExtractionError, BloombergParserError)


# ---------------------------------------------------------------------------
# Model construction
# ---------------------------------------------------------------------------

class TestModels:
    def test_parsed_company_data_default_construction(self):
        """ParsedCompanyData with no extraction populated still validates."""
        # ValidationReport's dataclass takes `file=Path` (NOT path=).
        report = ValidationReport(file=Path("dummy.xlsx"))

        data = ParsedCompanyData(
            source_path=Path("dummy.xlsx"),
            parsed_at=datetime.now(timezone.utc),
            validation_report=report,
        )
        assert data.ticker == ""
        assert data.config_currency == ""
        assert data.rv_comps is None
        assert isinstance(data.beta, BetaSheet)
        assert isinstance(data.dvd, DividendSheet)
        assert data.is_gbp_pence is False

    def test_sub_models_default_empty(self):
        """All sheet sub-models default to empty without errors."""
        assert BetaSheet().raw_beta is None
        assert DividendSheet().records == []
        assert EarningsEstimatesSheet().best_eps is None
        assert AnalystRecommendationsSheet().broker_recommendations == []
        assert PriceHistorySheet().series is None
        assert RVCompsSheet().peers == []

    def test_config_currency_accepts_any_string(self):
        """config_currency is plain str — non-USD values are valid at parse
        time (validator's job to ADVISE, not parser's job to refuse)."""
        report = ValidationReport(file=Path("dummy.xlsx"))
        data = ParsedCompanyData(
            source_path=Path("dummy.xlsx"),
            parsed_at=datetime.now(timezone.utc),
            validation_report=report,
            config_currency="NOK",
        )
        assert data.config_currency == "NOK"


# ---------------------------------------------------------------------------
# Validator-integration seam
# ---------------------------------------------------------------------------

class TestValidatorSeam:
    def test_parse_master_template_permissive_raises_on_config(self):
        """Master template has B3=None. PERMISSIVE proceeds past
        validator FAIL but CONFIG extraction raises."""
        with pytest.raises(WorkbookExtractionError, match="CONFIG"):
            parse_workbook(
                MASTER_TEMPLATE,
                validation_policy=ValidationPolicy.PERMISSIVE,
            )

    def test_parse_nonexistent_strict_raises_validation_error(self):
        """The validator catches missing files (FILE_NOT_FOUND code)
        and returns FAIL — STRICT policy promotes to
        WorkbookValidationError before extraction runs."""
        with pytest.raises(WorkbookValidationError):
            parse_workbook(Path("nonexistent.xlsx"))


# ---------------------------------------------------------------------------
# Sibling parser skeletons
# ---------------------------------------------------------------------------

class TestIndicesAndFX:
    def test_parse_indices_skeleton(self):
        """parse_indices_workbook returns a populated-but-empty model."""
        result = parse_indices_workbook(INDICES_TEMPLATE)
        assert result.source_path == INDICES_TEMPLATE
        assert result.obx is None
        assert result.spx is None

    def test_parse_fx_skeleton(self):
        result = parse_fx_workbook(FX_TEMPLATE)
        assert result.source_path == FX_TEMPLATE
        assert result.nokusd is None


# ---------------------------------------------------------------------------
# _read_scalar helper — unit tests against in-memory workbooks
# ---------------------------------------------------------------------------

def _make_ws(title: str, values: dict[str, object]) -> openpyxl.worksheet.worksheet.Worksheet:
    """Build a worksheet with `title` and the given coord -> value cells."""
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = title
    for coord, value in values.items():
        ws[coord] = value
    return ws


class TestReadScalar:
    @pytest.mark.parametrize("na_value", sorted(_NA_VALUES))
    def test_handles_each_known_na_variant(self, na_value: str):
        """Every enumerated _NA_VALUES entry returns None and is recorded."""
        ws = _make_ws("BETA", {"C6": na_value})
        na_cells: list[str] = []
        assert _read_scalar(ws, "C6", na_cells=na_cells) is None
        assert na_cells == ["BETA!C6"]

    def test_handles_unknown_hash_prefix(self):
        """Future Excel error codes are caught by the '#' prefix guard."""
        ws = _make_ws("EE", {"C8": "#FUTURE_ERROR_CODE!"})
        na_cells: list[str] = []
        assert _read_scalar(ws, "C8", na_cells=na_cells) is None
        assert na_cells == ["EE!C8"]

    def test_handles_none_cell(self):
        ws = _make_ws("BETA", {})  # C6 unset → None
        na_cells: list[str] = []
        assert _read_scalar(ws, "C6", na_cells=na_cells) is None
        assert na_cells == ["BETA!C6"]

    def test_handles_empty_string(self):
        ws = _make_ws("EE", {"C7": ""})
        na_cells: list[str] = []
        assert _read_scalar(ws, "C7", na_cells=na_cells) is None
        assert na_cells == ["EE!C7"]

    def test_handles_numeric_string_with_comma(self):
        """Bloomberg occasionally emits comma-grouped numbers; parse them."""
        ws = _make_ws("EE", {"C9": "1,234.5"})
        na_cells: list[str] = []
        assert _read_scalar(ws, "C9", na_cells=na_cells) == 1234.5
        assert na_cells == []

    def test_raises_on_unexpected_string(self):
        ws = _make_ws("EE", {"C8": "approx 1.2"})
        with pytest.raises(WorkbookExtractionError) as excinfo:
            _read_scalar(ws, "C8", na_cells=[])
        assert "EE!C8" in str(excinfo.value)
        assert "approx 1.2" in str(excinfo.value)

    def test_handles_int_value(self):
        ws = _make_ws("BETA", {"C6": 2})
        na_cells: list[str] = []
        result = _read_scalar(ws, "C6", na_cells=na_cells)
        assert result == 2.0
        assert isinstance(result, float)
        assert na_cells == []

    def test_handles_float_value(self):
        ws = _make_ws("BETA", {"C6": 1.524651})
        na_cells: list[str] = []
        assert _read_scalar(ws, "C6", na_cells=na_cells) == 1.524651
        assert na_cells == []


# ---------------------------------------------------------------------------
# Tier-1: BETA/EE extraction against the master template
#
# The template was saved without the Bloomberg add-in active, so cached
# BDP formula values are Excel "#NAME?" errors. data_only=True returns
# those as strings, which _read_scalar treats as NA-likes (via the '#'
# prefix guard). Result: all-None models with full na_cells coverage.
# ---------------------------------------------------------------------------

class TestExtractTemplate:
    def test_extract_beta_template_all_na(self):
        wb = openpyxl.load_workbook(MASTER_TEMPLATE, data_only=True, read_only=True)
        try:
            beta = _extract_beta(wb)
        finally:
            wb.close()
        assert beta.raw_beta is None
        assert beta.adjusted_beta is None
        assert beta.r_squared is None
        assert beta.na_cells == ["BETA!C6", "BETA!C7", "BETA!C8"]

    def test_extract_ee_template_all_na(self):
        wb = openpyxl.load_workbook(MASTER_TEMPLATE, data_only=True, read_only=True)
        try:
            ee = _extract_ee(wb)
        finally:
            wb.close()
        assert ee.best_eps is None
        assert ee.best_ltg_eeps is None
        assert ee.best_sales is None
        assert ee.best_ebitda is None
        assert ee.best_analyst_rating is None
        assert ee.na_cells == [
            "EE!C10", "EE!C11", "EE!C7", "EE!C8", "EE!C9",
        ]  # sorted lexicographically — matches the parser's sorted() at assembly


# ---------------------------------------------------------------------------
# Tier-2: BETA/EE extraction against the committed real-export fixture.
# EQNR's 2026-05-08 export has values for every scalar in BETA and EE
# (no #N/A). Tests assert types and plausible ranges, not exact numbers —
# Bloomberg cached values drift on re-save.
# ---------------------------------------------------------------------------

class TestExtractEqnrFixture:
    def test_extract_beta_eqnr_real_values(self):
        wb = openpyxl.load_workbook(EQNR_FIXTURE, data_only=True, read_only=True)
        try:
            beta = _extract_beta(wb)
        finally:
            wb.close()
        assert isinstance(beta.raw_beta, float)
        assert isinstance(beta.adjusted_beta, float)
        assert isinstance(beta.r_squared, float)
        assert 0 < beta.raw_beta < 3
        assert 0 < beta.adjusted_beta < 3
        assert 0 <= beta.r_squared <= 1
        assert beta.na_cells == []

    def test_extract_ee_eqnr_real_values(self):
        wb = openpyxl.load_workbook(EQNR_FIXTURE, data_only=True, read_only=True)
        try:
            ee = _extract_ee(wb)
        finally:
            wb.close()
        for field in (
            ee.best_eps,
            ee.best_ltg_eeps,
            ee.best_sales,
            ee.best_ebitda,
            ee.best_analyst_rating,
        ):
            assert isinstance(field, float)
        assert ee.best_eps > 0
        # best_ltg_eeps is a decimal (0.05 = 5%) due to the template's
        # `%` formula suffix; sanity-check it's not accidentally a percent.
        assert 0 < ee.best_ltg_eeps < 0.5
        assert ee.best_sales > 0
        assert ee.best_ebitda > 0
        assert 1.0 <= ee.best_analyst_rating <= 5.0
        assert ee.na_cells == []

    def test_parse_eqnr_full_smoke(self):
        """End-to-end: STRICT parse of the fixture populates BETA + EE,
        validator reports PASS or ADVISORY (not FAIL), and parser does
        not raise."""
        result = parse_workbook(EQNR_FIXTURE)
        assert result.ticker_short == "EQNR_NO"
        assert result.beta.raw_beta is not None
        assert result.ee.best_eps is not None
        assert result.beta.na_cells == []
        assert result.ee.na_cells == []
