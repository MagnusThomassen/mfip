"""
Tests for mfip.dashboard.zones.zone1.

Structural assertions only: imports succeed, page registration happens,
required ids are present, sensible defaults for the company selector,
date range, and theme toggle.

The test file imports zone1 directly to trigger dash.register_page;
the page registry is populated by import side effect.
"""

from __future__ import annotations

import datetime as _dt

import pytest

# Importing zone1 has side effects (register_page, layout build). Import
# here once so the page registry is populated for the registration test.
from mfip.dashboard.zones import zone1


def _walk(component):
    yield component
    children = getattr(component, "children", None)
    if children is None:
        return
    if isinstance(children, (list, tuple)):
        for child in children:
            yield from _walk(child)
    else:
        yield from _walk(children)


def _find_by_id(component, target_id: str):
    for node in _walk(component):
        if getattr(node, "id", None) == target_id:
            return node
    return None


def test_zone1_module_imports():
    # Already imported at module load — assert the module object exists.
    assert zone1 is not None
    assert hasattr(zone1, "layout")


def test_zone1_layout_contains_required_ids():
    required = [
        "zone1-top-bar",
        "mfip-logo",
        "pipeline-status",
        "pipeline-status-dot",
        "pipeline-status-label",
        "active-jobs-count",
        "alert-badges",
        "alert-badge-critical",
        "alert-badge-warning",
        "alert-badge-advisory",
        "unsent-alerts-indicator",
        "global-date-filter",
        "date-range-store",
        "date-preset-1y",
        "date-preset-3y",
        "date-preset-5y",
        "date-preset-max",
        "date-preset-custom",
        "date-picker-custom",
        "company-selector",
        "settings-icon",
        "settings-panel",
        "theme-toggle-radio",
        # NOTE: theme-css-applied moved to app-level layout (global side
        # effect of the clientside data-theme callback). Tested in test_app.py.
    ]
    missing = [
        component_id
        for component_id in required
        if _find_by_id(zone1.layout, component_id) is None
    ]
    assert not missing, f"Missing layout ids: {missing}"


def test_zone1_top_bar_height():
    header = _find_by_id(zone1.layout, "zone1-top-bar")
    assert header is not None
    assert header.style.get("height") == "60px"


def test_company_selector_default_equinor():
    selector = _find_by_id(zone1.layout, "company-selector")
    assert selector is not None
    assert selector.value == "EQNR"


def test_company_selector_options_are_six_universe_in_order():
    expected = ["EQNR", "DNB", "TEL", "NOVO B", "MSFT", "CKN"]
    selector = _find_by_id(zone1.layout, "company-selector")
    actual = [opt["value"] for opt in selector.options]
    assert actual == expected


def test_date_range_store_default_1y():
    store = _find_by_id(zone1.layout, "date-range-store")
    assert store is not None
    data = store.data
    assert data["preset"] == "1Y"
    start = _dt.date.fromisoformat(data["start"])
    end = _dt.date.fromisoformat(data["end"])
    span = (end - start).days
    assert 360 <= span <= 370, f"Expected ~365-day span, got {span}"


def test_theme_toggle_default_dark():
    radio = _find_by_id(zone1.layout, "theme-toggle-radio")
    assert radio is not None
    assert radio.value == "dark"


def test_zone1_local_theme_store_in_layout():
    store = _find_by_id(zone1.layout, "zone1-theme-radio-store")
    assert store is not None
    assert store.storage_type == "memory"


def test_theme_radio_writes_to_local_store():
    # Importing app ensures all @callback registrations have fired.
    from mfip.dashboard.app import app  # noqa: F401
    from dash._callback import GLOBAL_CALLBACK_MAP

    entry = GLOBAL_CALLBACK_MAP.get("zone1-theme-radio-store.data")
    assert entry is not None, (
        "No callback registered with Output('zone1-theme-radio-store', 'data')"
    )
    inputs = entry["inputs"]
    assert any(
        i["id"] == "theme-toggle-radio" and i["property"] == "value"
        for i in inputs
    ), f"Expected theme-toggle-radio.value as Input, got {inputs}"
