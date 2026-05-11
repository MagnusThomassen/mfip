"""
Tests for mfip.dashboard.theme.

Three groups:
1. apply_theme produces correct paper_bgcolor for dark mode.
2. apply_theme produces correct paper_bgcolor for light mode.
3. Token name sync — CSS variable names in ag-grid-overrides.css
   match Python dict keys in theme.py for both modes.

The third group is the load-bearing one: it catches drift between the
Python token set and the CSS variable set the moment it happens.
"""

from __future__ import annotations

import re
from pathlib import Path

import plotly.graph_objects as go
import pytest

from mfip.dashboard import theme


REPO_ROOT = Path(__file__).resolve().parent.parent
CSS_PATH = (
    REPO_ROOT / "mfip" / "dashboard" / "assets" / "ag-grid-overrides.css"
)


# ---------------------------------------------------------------------------
# apply_theme — Plotly figure output
# ---------------------------------------------------------------------------

def test_apply_theme_dark_sets_paper_bgcolor():
    fig = go.Figure()
    apply = theme.apply_theme(fig, "dark")
    assert apply.layout.paper_bgcolor == "#0D1117"
    assert apply.layout.plot_bgcolor == "#161B22"
    assert apply.layout.font.color == "#E6EDF3"


def test_apply_theme_light_sets_paper_bgcolor():
    fig = go.Figure()
    apply = theme.apply_theme(fig, "light")
    assert apply.layout.paper_bgcolor == "#FBFCFD"
    assert apply.layout.plot_bgcolor == "#FFFFFF"
    assert apply.layout.font.color == "#1F2328"


def test_apply_theme_returns_same_figure_object():
    """apply_theme mutates in place; callbacks rely on returning the same fig."""
    fig = go.Figure()
    returned = theme.apply_theme(fig, "dark")
    assert returned is fig


def test_apply_theme_unknown_mode_raises():
    fig = go.Figure()
    with pytest.raises(ValueError):
        theme.apply_theme(fig, "midnight")  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# Token name sync — CSS variables vs Python dict keys
# ---------------------------------------------------------------------------

# Pattern matches `--token-name:` declarations. We then filter out
# AG Grid's own --ag-* variables to leave only MFIP tokens.
CSS_VAR_PATTERN = re.compile(r"--([a-z0-9-]+)\s*:", re.IGNORECASE)


def _extract_mfip_tokens_from_css_block(block: str) -> set[str]:
    """Return the set of MFIP token names declared in a CSS block."""
    names = set(CSS_VAR_PATTERN.findall(block))
    # Drop AG Grid's own variables (--ag-*). MFIP tokens never start with `ag-`.
    return {n for n in names if not n.startswith("ag-")}


def _split_css_by_selector(css: str) -> dict[str, str]:
    """
    Crudely split the CSS into blocks keyed by selector.
    Sufficient for two-selector files like ag-grid-overrides.css.
    """
    blocks: dict[str, str] = {}
    pattern = re.compile(
        r"\.(ag-theme-alpine(?:-dark)?)\s*\{([^}]*)\}",
        re.DOTALL,
    )
    for match in pattern.finditer(css):
        selector, body = match.group(1), match.group(2)
        blocks[selector] = body
    return blocks


def test_css_file_exists():
    assert CSS_PATH.is_file(), f"Expected CSS file at {CSS_PATH}"


def test_dark_tokens_match_python():
    css = CSS_PATH.read_text(encoding="utf-8")
    blocks = _split_css_by_selector(css)
    assert "ag-theme-alpine-dark" in blocks, (
        "Missing .ag-theme-alpine-dark block in ag-grid-overrides.css"
    )
    css_tokens = _extract_mfip_tokens_from_css_block(
        blocks["ag-theme-alpine-dark"]
    )
    py_tokens = set(theme.DARK.keys())

    missing_in_css = py_tokens - css_tokens
    missing_in_py = css_tokens - py_tokens
    assert not missing_in_css, (
        f"Tokens in theme.py DARK but not declared in CSS dark block: "
        f"{sorted(missing_in_css)}"
    )
    assert not missing_in_py, (
        f"Tokens in CSS dark block but not in theme.py DARK: "
        f"{sorted(missing_in_py)}"
    )


def test_light_tokens_match_python():
    css = CSS_PATH.read_text(encoding="utf-8")
    blocks = _split_css_by_selector(css)
    assert "ag-theme-alpine" in blocks, (
        "Missing .ag-theme-alpine block in ag-grid-overrides.css"
    )
    css_tokens = _extract_mfip_tokens_from_css_block(
        blocks["ag-theme-alpine"]
    )
    py_tokens = set(theme.LIGHT.keys())

    missing_in_css = py_tokens - css_tokens
    missing_in_py = css_tokens - py_tokens
    assert not missing_in_css, (
        f"Tokens in theme.py LIGHT but not declared in CSS light block: "
        f"{sorted(missing_in_css)}"
    )
    assert not missing_in_py, (
        f"Tokens in CSS light block but not in theme.py LIGHT: "
        f"{sorted(missing_in_py)}"
    )


def test_dark_and_light_have_same_token_names():
    """Both modes must expose the same token set — only hex values differ."""
    assert set(theme.DARK.keys()) == set(theme.LIGHT.keys())
