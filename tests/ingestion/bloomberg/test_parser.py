"""Parser scaffolding tests.

Functional per-sheet extraction tests come in PR #63 onward; this
file covers the scaffolding: public API surface, model construction,
validator integration seam, exception hierarchy, CLI smoke.
"""

from datetime import datetime, timezone
from pathlib import Path

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
