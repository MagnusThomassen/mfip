"""
Zone 1 — Command Centre. Top-bar chrome that mounts at /.

All data here is placeholder for Session 6. Pipeline state, alert counts,
job counts, and the alert feed body are wired in later sessions when
the agent layer and alert subsystem land. The display surfaces and
their toggle behaviours are real now so later work has somewhere to
write into.

Spec source: 05_DASHBOARD_SPEC.docx Zone 1 + Global Date Filter sections.
"""

from __future__ import annotations

import datetime as _dt

import dash
from dash import (
    Input,
    Output,
    State,
    callback,
    callback_context,
    dcc,
    html,
    no_update,
)
from dateutil.relativedelta import relativedelta


# ---------------------------------------------------------------------------
# Module-level constants
# ---------------------------------------------------------------------------

_TICKER_SPAN_STYLE = {"fontFamily": "var(--font-mono)", "marginLeft": "4px"}


def _company_label(name: str, ticker: str):
    return html.Span(
        [name, html.Span(f"({ticker})", style=_TICKER_SPAN_STYLE)]
    )


COMPANIES = [
    {"value": "EQNR", "label": _company_label("Equinor ", "EQNR")},
    {"value": "DNB", "label": _company_label("DNB ", "DNB")},
    {"value": "TEL", "label": _company_label("Telenor ", "TEL")},
    {"value": "NOVO B", "label": _company_label("Novo Nordisk ", "NOVO B")},
    {"value": "MSFT", "label": _company_label("Microsoft ", "MSFT")},
    {"value": "CKN", "label": _company_label("Clarkson ", "CKN")},
]

# Spec-order ticker list — used by the test suite and to index COMPANIES
COMPANY_TICKERS = [c["value"] for c in COMPANIES]

DATE_PRESETS = ["1Y", "3Y", "5Y", "MAX", "Custom"]


def _preset_range(preset: str) -> tuple[str, str]:
    """Resolve a preset name to (start_iso, end_iso). MAX reaches back 20y."""
    today = _dt.date.today()
    if preset == "1Y":
        start = today - relativedelta(years=1)
    elif preset == "3Y":
        start = today - relativedelta(years=3)
    elif preset == "5Y":
        start = today - relativedelta(years=5)
    elif preset == "MAX":
        start = today - relativedelta(years=20)
    else:  # "Custom" — caller supplies dates
        start = today - relativedelta(years=1)
    return start.isoformat(), today.isoformat()


_INITIAL_START, _INITIAL_END = _preset_range("1Y")
INITIAL_DATE_RANGE = {
    "preset": "1Y",
    "start": _INITIAL_START,
    "end": _INITIAL_END,
}


# ---------------------------------------------------------------------------
# Layout
# ---------------------------------------------------------------------------

_TOP_BAR_HEIGHT = "60px"

_PRESET_BUTTON_STYLE = {
    "padding": "4px 10px",
    "border": "1px solid var(--border-subtle)",
    "background": "var(--bg-surface-raised)",
    "color": "var(--text-primary)",
    "cursor": "pointer",
    "fontFamily": "var(--font-sans)",
    "fontSize": "12px",
}

_BADGE_BASE_STYLE = {
    "padding": "2px 10px",
    "borderRadius": "999px",
    "border": "none",
    "cursor": "pointer",
    "fontFamily": "var(--font-mono)",
    "fontVariantNumeric": "tabular-nums",
    "fontSize": "12px",
    "color": "var(--text-primary)",
}

_HEADER_STYLE = {
    "height": _TOP_BAR_HEIGHT,
    "display": "flex",
    "alignItems": "center",
    "background": "var(--bg-surface)",
    "borderBottom": "1px solid var(--border-subtle)",
}


def _date_filter():
    return html.Div(
        id="global-date-filter",
        style={"display": "flex", "alignItems": "center", "gap": "6px"},
        children=[
            dcc.Store(id="date-range-store", data=INITIAL_DATE_RANGE),
            html.Button("1Y", id="date-preset-1y", n_clicks=0, style=_PRESET_BUTTON_STYLE),
            html.Button("3Y", id="date-preset-3y", n_clicks=0, style=_PRESET_BUTTON_STYLE),
            html.Button("5Y", id="date-preset-5y", n_clicks=0, style=_PRESET_BUTTON_STYLE),
            html.Button("MAX", id="date-preset-max", n_clicks=0, style=_PRESET_BUTTON_STYLE),
            html.Button("Custom", id="date-preset-custom", n_clicks=0, style=_PRESET_BUTTON_STYLE),
            dcc.DatePickerRange(
                id="date-picker-custom",
                style={"display": "none"},
                start_date=_INITIAL_START,
                end_date=_INITIAL_END,
            ),
        ],
    )


def _settings_panel():
    return html.Div(
        id="settings-panel",
        style={
            "display": "none",
            "position": "absolute",
            "top": _TOP_BAR_HEIGHT,
            "right": "16px",
            "background": "var(--bg-surface-raised)",
            "border": "1px solid var(--border-subtle)",
            "padding": "12px",
            "minWidth": "160px",
            "zIndex": 1000,
        },
        children=[
            html.Div("Theme", className="text-label"),
            dcc.RadioItems(
                id="theme-toggle-radio",
                options=[
                    {"label": "Dark", "value": "dark"},
                    {"label": "Light", "value": "light"},
                    {"label": "System", "value": "system"},
                ],
                value="dark",
                labelStyle={"display": "block", "marginTop": "4px"},
            ),
        ],
    )


layout = html.Div(
    style={"position": "relative"},
    children=[
        html.Header(
            id="zone1-top-bar",
            className="density-roomy",
            style=_HEADER_STYLE,
            children=[
                html.Div(id="mfip-logo", className="text-h1", children="MFIP"),
                # b. Pipeline status indicator
                html.Div(
                    id="pipeline-status",
                    **{"data-state": "idle"},
                    style={"display": "flex", "alignItems": "center", "gap": "6px"},
                    children=[
                        html.Span(
                            id="pipeline-status-dot",
                            style={
                                "width": "10px",
                                "height": "10px",
                                "borderRadius": "50%",
                                "background": "var(--text-muted)",
                                "display": "inline-block",
                            },
                        ),
                        html.Span(
                            id="pipeline-status-label",
                            children="Idle",
                            className="text-label",
                            style={"color": "var(--text-secondary)"},
                        ),
                    ],
                ),
                # c. Active Jobs counter
                html.Div(
                    id="active-jobs-count",
                    children="0",
                    title="Extraction: 0  |  Modelling: 0  |  Complete: 0",
                    className="text-data-md",
                ),
                # d. Alert badges
                html.Div(
                    id="alert-badges",
                    style={"display": "flex", "gap": "6px"},
                    children=[
                        html.Button(
                            "0",
                            id="alert-badge-critical",
                            n_clicks=0,
                            style={**_BADGE_BASE_STYLE, "background": "var(--accent-critical)"},
                        ),
                        html.Button(
                            "0",
                            id="alert-badge-warning",
                            n_clicks=0,
                            style={**_BADGE_BASE_STYLE, "background": "var(--accent-hold)"},
                        ),
                        html.Button(
                            "0",
                            id="alert-badge-advisory",
                            n_clicks=0,
                            style={
                                **_BADGE_BASE_STYLE,
                                "background": "var(--bg-surface-raised)",
                                "color": "var(--text-secondary)",
                                "border": "1px solid var(--accent-hold)",
                            },
                        ),
                    ],
                ),
                # e. Unsent Alerts indicator (hidden when queue empty)
                # TODO: opens queue view with retry/dismiss controls per alert (out of scope for Session 6)
                html.Div(
                    id="unsent-alerts-indicator",
                    children="Unsent: 0",
                    className="text-label",
                    style={"display": "none", "color": "var(--accent-sell)"},
                ),
                # f. Global Date Filter
                _date_filter(),
                # g. Company Selector
                html.Div(
                    style={"width": "240px", "marginLeft": "auto"},
                    children=[
                        dcc.Dropdown(
                            id="company-selector",
                            options=COMPANIES,
                            value="EQNR",
                            clearable=False,
                        ),
                    ],
                ),
                # h. Settings icon
                html.Button(
                    "⚙",
                    id="settings-icon",
                    n_clicks=0,
                    style={
                        "background": "transparent",
                        "border": "none",
                        "color": "var(--text-primary)",
                        "fontSize": "20px",
                        "cursor": "pointer",
                        "padding": "0 8px",
                    },
                ),
            ],
        ),
        # i. Settings panel (positioned absolutely, hidden by default)
        _settings_panel(),
    ],
)


# ---------------------------------------------------------------------------
# Callbacks
# ---------------------------------------------------------------------------

# a. Alert badge clicks → toggle alert-feed-panel display
@callback(
    Output("alert-feed-panel", "style"),
    Input("alert-badge-critical", "n_clicks"),
    Input("alert-badge-warning", "n_clicks"),
    Input("alert-badge-advisory", "n_clicks"),
    State("alert-feed-panel", "style"),
    prevent_initial_call=True,
)
def _toggle_alert_feed(_n_crit, _n_warn, _n_adv, current_style):
    style = dict(current_style or {})
    style["display"] = "none" if style.get("display") == "block" else "block"
    return style


# b. Settings icon click → toggle settings-panel display
@callback(
    Output("settings-panel", "style"),
    Input("settings-icon", "n_clicks"),
    State("settings-panel", "style"),
    prevent_initial_call=True,
)
def _toggle_settings_panel(_n, current_style):
    style = dict(current_style or {})
    style["display"] = "none" if style.get("display") == "block" else "block"
    return style


# c. Date preset buttons + custom picker → date-range-store
#    Custom button also reveals the picker; other presets hide it.
@callback(
    Output("date-range-store", "data"),
    Output("date-picker-custom", "style"),
    Input("date-preset-1y", "n_clicks"),
    Input("date-preset-3y", "n_clicks"),
    Input("date-preset-5y", "n_clicks"),
    Input("date-preset-max", "n_clicks"),
    Input("date-preset-custom", "n_clicks"),
    Input("date-picker-custom", "start_date"),
    Input("date-picker-custom", "end_date"),
    State("date-picker-custom", "style"),
    prevent_initial_call=True,
)
def _update_date_range(_n1, _n3, _n5, _nmax, _ncust, start, end, picker_style):
    triggered = callback_context.triggered_id
    picker_visible = dict(picker_style or {"display": "none"})

    preset_map = {
        "date-preset-1y": "1Y",
        "date-preset-3y": "3Y",
        "date-preset-5y": "5Y",
        "date-preset-max": "MAX",
    }

    if triggered in preset_map:
        preset = preset_map[triggered]
        s, e = _preset_range(preset)
        picker_visible["display"] = "none"
        return {"preset": preset, "start": s, "end": e}, picker_visible

    if triggered == "date-preset-custom":
        picker_visible["display"] = "inline-block"
        return no_update, picker_visible

    if triggered == "date-picker-custom" or triggered is None:
        # Picker change. Only write to the store if both dates are present.
        if start and end:
            return (
                {"preset": "Custom", "start": str(start), "end": str(end)},
                picker_visible,
            )

    return no_update, no_update


# DEFERRED to Session 7 — see decisions.md 2026-05-11 entry on
# cross-layout callback Inputs. The theme toggle UI still renders;
# clicking the radio writes to its own value but does not propagate
# to theme-mode-store yet. theme-css-applied clientside callback
# still runs on app boot to apply the initial dark mode.
#
# @callback(
#     Output("theme-mode-store", "data"),
#     Input("theme-toggle-radio", "value"),
#     Input("theme-system-pref-store", "data"),
#     prevent_initial_call=True,
# )
# def _theme_toggle_to_mode(radio_value, system_pref):
#     if radio_value == "system":
#         return system_pref or "dark"
#     return radio_value


# NOTE: the data-theme attribute application (mode store → <html>) is a
# global side effect, not zone-specific. It lives in app.py.


# ---------------------------------------------------------------------------
# Page registration
# ---------------------------------------------------------------------------
# Must come last: with pages_folder="" Dash does not auto-discover the
# module-level `layout` attribute, so it must be passed explicitly.
dash.register_page(
    __name__,
    path="/",
    layout=layout,
    name="Command Centre",
)
