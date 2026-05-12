"""
Tests for mfip.dashboard.app — routing shell.

Three checks: app constructs without exception, the layout exposes
every id later code depends on, and the theme-mode-store ships with
"dark" as its initial value.

Tests do not call app.run(). Construction + layout introspection only.
"""

from __future__ import annotations

import dash
from dash import Dash

from mfip.dashboard.app import app


def _walk(component):
    """Yield every component in a Dash layout tree, including the root."""
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
    """Return the first component in the tree with matching id, or None."""
    for node in _walk(component):
        if getattr(node, "id", None) == target_id:
            return node
    return None


def test_app_instantiates():
    assert isinstance(app, Dash)


def test_layout_contains_required_ids():
    """Required ids must be present, and dash.page_container must be in
    the tree because use_pages=True wires internal _pages_* callbacks
    that target it."""
    required = [
        "url",
        "theme-mode-store",
        "theme-system-pref-store",
        "theme-css-applied",
        "alert-feed-panel",
    ]
    missing = [
        component_id
        for component_id in required
        if _find_by_id(app.layout, component_id) is None
    ]
    assert not missing, f"Missing layout ids: {missing}"
    assert any(
        node is dash.page_container for node in _walk(app.layout)
    ), "dash.page_container missing from layout"


def test_theme_store_default_dark():
    store = _find_by_id(app.layout, "theme-mode-store")
    assert store is not None
    assert store.data == "dark"


def test_local_to_global_theme_store_callback():
    from dash._callback import GLOBAL_CALLBACK_MAP

    entry = GLOBAL_CALLBACK_MAP.get("theme-mode-store.data")
    assert entry is not None, (
        "No callback registered with Output('theme-mode-store', 'data')"
    )
    assert any(
        i["id"] == "zone1-theme-radio-store" and i["property"] == "data"
        for i in entry["inputs"]
    ), f"Expected zone1-theme-radio-store.data as Input, got {entry['inputs']}"


def test_theme_mode_store_local_storage():
    store = _find_by_id(app.layout, "theme-mode-store")
    assert store is not None
    assert store.storage_type == "local"
