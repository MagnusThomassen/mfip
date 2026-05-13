"""
Home page — operational dashboard stub at /.

Placeholder for the future Project Dashboard View (operational stats,
build phase status, links to repo / decisions log / ideas list).
Real Home contents are deferred — see ideas.md "2026-05-10 — Project
Dashboard View" entry (RESOLVED-PARTIALLY) and the 2026-05-13 routing
architecture decision in decisions.md.

The stub exists so the route registers cleanly and Magnus has a place
to land when opening the app, with a clear path to the analysis surface.
"""

from __future__ import annotations

import dash
from dash import dcc, html

layout = html.Div(
    [
        html.H1("MFIP — Home", className="text-h1"),
        html.P(
            "Operational dashboard placeholder. "
            "Real contents to be designed once /analysis is in routine use.",
            className="text-body",
        ),
        dcc.Link(
            "Open analysis dashboard →",
            href="/analysis",
            className="text-body",
        ),
    ],
    style={"padding": "var(--space-roomy)"},
)

dash.register_page(
    __name__,
    path="/",
    layout=layout,
    name="Home",
)
