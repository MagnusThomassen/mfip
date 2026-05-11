"""
MFIP dashboard — Dash app instance and top-level layout.

Routing shell only. No zone content lives here — zones mount into
the `page-content` slot via callbacks (or, later, via the page
registry enabled by `use_pages=True`).

Two stores own theme state:
- theme-mode-store: persisted across reloads (localStorage). Drives
  every figure and grid theme. Default "dark".
- theme-system-pref-store: in-memory mirror of the OS
  prefers-color-scheme value. The toggle in Zone 1 settings (Part 2)
  decides whether to follow this or the user's explicit override.

A single inline clientside callback subscribes to the OS theme
MediaQueryList so theme-system-pref-store updates when the OS flips
at sunset. The callback fires on dcc.Location pathname changes
(including initial load); a window-level guard prevents
re-subscribing the listener on subsequent navigations.

Spec source: 05_DASHBOARD_SPEC.docx v1.2; routing per
decisions.md 2026-05-11 "Phase 1 routing decision".
"""

from __future__ import annotations

import dash
from dash import Dash, Input, Output, clientside_callback, dcc, html

app = Dash(
    __name__,
    use_pages=True,
    pages_folder="",
    assets_folder="assets",
    suppress_callback_exceptions=True,
)

# Import zone modules so their dash.register_page calls populate the
# page registry. With pages_folder="" there's no auto-discovery — each
# zone must be imported explicitly. Add a line per new zone here.
from mfip.dashboard.zones import zone1  # noqa: E402, F401

app.layout = html.Div(
    [
        dcc.Location(id="url", refresh=False),
        dcc.Store(
            id="theme-mode-store",
            storage_type="local",
            data="dark",
        ),
        dcc.Store(
            id="theme-system-pref-store",
            storage_type="memory",
        ),
        # Dummy Output for the data-theme clientside callback below.
        # Lives in app.py because the callback's effect (setting an
        # attribute on <html>) is global, not zone-specific.
        dcc.Store(id="theme-css-applied", storage_type="memory"),
        dash.page_container,
        html.Div(id="alert-feed-panel"),
    ]
)


# Read the OS prefers-color-scheme value into the system-pref store and
# subscribe to changes. The MediaQueryList listener is attached at most
# once per browser session — guarded by a window-level flag because the
# callback re-fires on every URL navigation.
clientside_callback(
    """
    function(_pathname) {
        const mql = window.matchMedia('(prefers-color-scheme: dark)');
        if (!window.__mfipThemeListenerAttached) {
            mql.addEventListener('change', function(e) {
                // Trigger a synthetic navigation event to re-fire this
                // callback when the OS theme flips. Dash stores update
                // through callbacks, so we need a callback re-run to
                // write the new value to theme-system-pref-store.
                window.dispatchEvent(new Event('mfip-theme-change'));
            });
            window.addEventListener('mfip-theme-change', function() {
                const current = window.matchMedia(
                    '(prefers-color-scheme: dark)'
                ).matches ? 'dark' : 'light';
                // Write directly through the dash_clientside store API.
                // The store update via return value below covers the
                // initial load; this covers MediaQuery changes after.
                const store = document.querySelector(
                    '[id="theme-system-pref-store"]'
                );
                if (store && window.dash_clientside) {
                    // Two write paths to theme-system-pref-store:
                    //   1. Callback return value — fires on mount (and URL change, harmless)
                    //   2. set_props from MediaQuery change handler — fires when OS theme flips mid-session
                    // Both are needed because Dash callbacks don't re-fire on browser events.
                    window.dash_clientside.set_props(
                        'theme-system-pref-store',
                        {data: current}
                    );
                }
            });
            window.__mfipThemeListenerAttached = true;
        }
        return mql.matches ? 'dark' : 'light';
    }
    """,
    Output("theme-system-pref-store", "data"),
    Input("url", "pathname"),
)


# Mode store → document data-theme attribute. Sets the source-of-truth
# attribute on <html> so any [data-theme="dark"] / [data-theme="light"]
# CSS selector resolves. Global side effect → lives here, not in a zone.
clientside_callback(
    """
    function(mode) {
        if (mode) {
            document.documentElement.setAttribute('data-theme', mode);
        }
        return mode;
    }
    """,
    Output("theme-css-applied", "data"),
    Input("theme-mode-store", "data"),
)
