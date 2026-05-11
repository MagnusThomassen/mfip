"""
MFIP theme module — single source of truth for all colors.

Every color in the application is referenced by semantic token name through
this module. No raw hex appears anywhere outside this file.

Two complete token sets are defined: dark (default) and light. Both are
flat dicts keyed by token name. Token names match the CSS variables in
assets/ag-grid-overrides.css exactly (verified by test_theme.py).

The apply_theme(fig, mode) helper mutates a Plotly figure in place,
setting paper_bgcolor, plot_bgcolor, font color, and axis colors from
the active token set. Every figure-producing callback in the dashboard
ends with `return apply_theme(fig, mode)`.

Spec source: 05_DASHBOARD_SPEC.docx v1.2, Visual Identity block.
"""

from __future__ import annotations

from typing import Literal

Mode = Literal["dark", "light"]


# ---------------------------------------------------------------------------
# Token sets
# ---------------------------------------------------------------------------
# Flat naming convention: spec's `bg.canvas` becomes `bg-canvas` here.
# This matches CSS variable naming exactly (dots are illegal in CSS vars).
# Token names are stable — any new color need is satisfied by adding a token,
# not by inlining a hex value.

DARK: dict[str, str] = {
    # Surfaces
    "bg-canvas": "#0D1117",
    "bg-surface": "#161B22",
    "bg-surface-raised": "#1C232C",
    # Borders
    "border-subtle": "#30363D",
    "border-strong": "#444C56",
    # Text
    "text-primary": "#E6EDF3",
    "text-secondary": "#8B949E",
    "text-muted": "#6E7681",
    # Accents (semantic — never decorative)
    "accent-buy": "#3FB950",
    "accent-sell": "#F85149",
    "accent-hold": "#D29922",
    "accent-interactive": "#58A6FF",
    "accent-critical": "#F85149",
    # Chart series palette (eight colors, then re-use with pattern variation)
    "chart-series-1": "#58A6FF",
    "chart-series-2": "#D29922",
    "chart-series-3": "#A371F7",
    "chart-series-4": "#3FB950",
    "chart-series-5": "#F85149",
    "chart-series-6": "#39C5CF",
    "chart-series-7": "#E780C5",
    "chart-series-8": "#8B949E",
}

LIGHT: dict[str, str] = {
    # Surfaces
    "bg-canvas": "#FBFCFD",
    "bg-surface": "#FFFFFF",
    "bg-surface-raised": "#F4F6F8",
    # Borders
    "border-subtle": "#E1E4E8",
    "border-strong": "#BCC2CA",
    # Text
    "text-primary": "#1F2328",
    "text-secondary": "#656D76",
    "text-muted": "#8C959F",
    # Accents
    "accent-buy": "#1A7F37",
    "accent-sell": "#CF222E",
    "accent-hold": "#9A6700",
    "accent-interactive": "#0969DA",
    "accent-critical": "#CF222E",
    # Chart series
    "chart-series-1": "#0969DA",
    "chart-series-2": "#9A6700",
    "chart-series-3": "#6639BA",
    "chart-series-4": "#1A7F37",
    "chart-series-5": "#CF222E",
    "chart-series-6": "#0E7C86",
    "chart-series-7": "#B4378F",
    "chart-series-8": "#656D76",
}

TOKENS: dict[Mode, dict[str, str]] = {
    "dark": DARK,
    "light": LIGHT,
}


# ---------------------------------------------------------------------------
# Plotly figure theming
# ---------------------------------------------------------------------------

def apply_theme(fig, mode: Mode):
    """
    Apply MFIP theme tokens to a Plotly figure.

    Mutates `fig` in place and returns it, so callbacks can end with:
        return apply_theme(fig, mode)

    Sets paper_bgcolor, plot_bgcolor, font color, and axis colors
    (tickcolor, gridcolor, linecolor, zerolinecolor) on every x and y
    axis present in the layout. Does not touch trace colors — those
    are set explicitly by the callback from the chart-series-* tokens.
    """
    if mode not in TOKENS:
        raise ValueError(
            f"Unknown theme mode: {mode!r}. Expected 'dark' or 'light'."
        )

    t = TOKENS[mode]

    fig.update_layout(
        paper_bgcolor=t["bg-canvas"],
        plot_bgcolor=t["bg-surface"],
        font=dict(color=t["text-primary"]),
    )

    # Axis colors apply to every x*/y* axis. Plotly stores them as
    # layout.xaxis, layout.xaxis2, etc. update_xaxes / update_yaxes
    # with no selector applies to all.
    fig.update_xaxes(
        tickcolor=t["text-secondary"],
        linecolor=t["border-subtle"],
        gridcolor=t["border-subtle"],
        zerolinecolor=t["border-subtle"],
    )
    fig.update_yaxes(
        tickcolor=t["text-secondary"],
        linecolor=t["border-subtle"],
        gridcolor=t["border-subtle"],
        zerolinecolor=t["border-subtle"],
    )

    return fig
