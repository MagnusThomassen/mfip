"""Pydantic models for the Bloomberg parser output.

The parser's public contract is `ParsedCompanyData` — a Pydantic v2
BaseModel that downstream agents (Reconciliation Engine, Comps Agent,
Chief Analyst, etc.) consume as the handoff schema per CONTEXT.md.

Sub-models exist per Bloomberg sheet (BETA, DVD, EE, ANR, HP_Monthly,
HP_Daily, RV_Comps). Each carries the data plus extraction-time
metadata (NA cells, missing/present columns, etc.) that downstream
agents need without re-running the parser.

PR #62b ships the skeleton; extraction is filled in PR #63 onward.
"""

from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd
from pydantic import BaseModel, ConfigDict, Field

# Direct import — no circular dependency (validator imports only from
# archive_lookup, not from this module).
from mfip.ingestion.bloomberg.validator import Finding, ValidationReport


# ---------------------------------------------------------------------------
# Per-sheet sub-models
# ---------------------------------------------------------------------------

class _BaseSheetModel(BaseModel):
    """Common Pydantic config for all sheet models.

    `arbitrary_types_allowed=True` is required for pandas.Series /
    pandas.DataFrame fields. The trade-off: Pydantic does not validate
    the *internal* shape of pandas objects, only that the field is
    an instance of the right type. Internal validation (dtypes, index
    shape) is the parser's responsibility at extraction time.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)


class BetaSheet(_BaseSheetModel):
    """BETA sheet — scalar regression metrics. Local currency."""

    raw_beta: float | None = None
    adjusted_beta: float | None = None
    r_squared: float | None = None
    na_cells: list[str] = Field(default_factory=list)


class DividendRecord(BaseModel):
    """One row of the DVD bulk return."""

    declared_date: datetime | None = None
    ex_date: datetime | None = None
    record_date: datetime | None = None
    payable_date: datetime | None = None
    dividend_amount: float | None = None
    dividend_type: str | None = None
    frequency: str | None = None


class DividendSheet(_BaseSheetModel):
    """DVD sheet — bulk dividend history via DVD_HIST_ALL."""

    records: list[DividendRecord] = Field(default_factory=list)


class EarningsEstimatesSheet(_BaseSheetModel):
    """EE sheet — forward consensus scalars (1FY)."""

    best_eps: float | None = None
    best_ltg_eeps: float | None = None
    best_sales: float | None = None
    best_ebitda: float | None = None
    best_analyst_rating: float | None = None
    na_cells: list[str] = Field(default_factory=list)


class BrokerRecord(BaseModel):
    """One row of the ANR broker-level recommendation table."""

    broker_name: str | None = None
    recommendation: str | None = None
    target_price: float | None = None
    rating_date: datetime | None = None


class AnalystRecommendationsSheet(_BaseSheetModel):
    """ANR sheet — analyst recommendation scalars + broker table.

    Currency: local listing currency (NOT USD). CKN is in GBp (pence).
    The parser surfaces raw values; currency normalisation is downstream.
    """

    buys_pct: float | None = None
    holds_pct: float | None = None
    sells_pct: float | None = None
    total_buys: int | None = None
    total_holds: int | None = None
    total_sells: int | None = None
    rating: float | None = None
    target_price: float | None = None
    last_price: float | None = None
    return_potential: float | None = None
    ltm_return: float | None = None
    broker_recommendations: list[BrokerRecord] = Field(default_factory=list)
    na_cells: list[str] = Field(default_factory=list)


class PriceHistorySheet(_BaseSheetModel):
    """HP_Monthly or HP_Daily — date-indexed close price series."""

    series: pd.Series | None = None
    # Series index = pd.DatetimeIndex (name='Date'); values = float
    # (name='PX_LAST'). Empty Series if extraction yielded no rows;
    # None if sheet absent (shouldn't happen for HP_Monthly /
    # HP_Daily — validator FAILs on missing required sheets).
    na_cells: list[str] = Field(default_factory=list)


class RVCompsSheet(_BaseSheetModel):
    """RV_Comps sheet — peer multiples from Bloomberg RV terminal screen.

    Columns are terminal-side contract (saved as a named Bloomberg
    layout). Parser matches by header name, not position.

    `peers` uses `dict[str, Any]` because the column set mixes types
    (Ticker and Name are strings; multiples and growth metrics are
    numeric; some cells are None/#N/A). Restricting to numeric values
    would mis-type Ticker/Name; strongly-typed sub-models would lock
    in a contract that the terminal-side layout doesn't enforce.
    """

    peers: list[dict[str, Any]] = Field(default_factory=list)
    present_columns: list[str] = Field(default_factory=list)
    missing_baseline_columns: list[str] = Field(default_factory=list)
    pending_planned_columns: list[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Top-level models
# ---------------------------------------------------------------------------

class ParsedCompanyData(_BaseSheetModel):
    """Parser output for a single Bloomberg company workbook.

    This is the handoff schema between the parser and every downstream
    agent that consumes Bloomberg data. Per CONTEXT.md, schema
    violations trigger a Security Council Advisory at the agent
    boundary — but at the parser layer itself, schema construction
    failures raise WorkbookExtractionError.

    The validator's report is carried forward in `validation_report`
    so consumers can inspect contract-conformance evidence without
    re-running the validator. Advisory findings are also surfaced in
    `advisories` for convenience.
    """

    # Provenance
    source_path: Path
    parsed_at: datetime
    validation_report: ValidationReport
    advisories: list[Finding] = Field(default_factory=list)

    # CONFIG-derived
    ticker: str = ""               # Bloomberg-form, e.g. "EQNR NO Equity"
    ticker_short: str = ""         # Filename-form, e.g. "EQNR_NO"
    config_currency: str = ""      # "USD" on saved files; "" or other = ADVISORY
                                   # at the validator level (NOT parser-level FAIL).
                                   # Plain str — not Literal — because validator
                                   # treats non-USD as ADVISORY, not FAIL, so the
                                   # parser may legitimately see other values.
    listing_currency: str = ""     # Derived from ticker suffix; empty until #65

    # Currency-handling artefacts
    is_gbp_pence: bool = False     # True only for CKN; set in PR #65

    # Per-sheet data (all default-empty in PR #62b)
    beta: BetaSheet = Field(default_factory=BetaSheet)
    dvd: DividendSheet = Field(default_factory=DividendSheet)
    ee: EarningsEstimatesSheet = Field(default_factory=EarningsEstimatesSheet)
    anr: AnalystRecommendationsSheet = Field(default_factory=AnalystRecommendationsSheet)
    hp_monthly: PriceHistorySheet = Field(default_factory=PriceHistorySheet)
    hp_daily: PriceHistorySheet = Field(default_factory=PriceHistorySheet)
    rv_comps: RVCompsSheet | None = None  # None when sheet absent (pre-lab templates)


class ParsedIndicesData(_BaseSheetModel):
    """Parser output for the Indices workbook (4 index series)."""

    source_path: Path
    parsed_at: datetime
    obx: pd.Series | None = None
    omxc25: pd.Series | None = None
    ukx: pd.Series | None = None
    spx: pd.Series | None = None


class ParsedFXData(_BaseSheetModel):
    """Parser output for the FX workbook (3 FX cross series)."""

    source_path: Path
    parsed_at: datetime
    nokusd: pd.Series | None = None
    dkkusd: pd.Series | None = None
    gbpusd: pd.Series | None = None
