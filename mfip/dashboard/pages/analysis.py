"""
Analysis page — multi-zone investment analysis surface at /analysis.

Composes Zone 1 (Command Centre) plus placeholder containers for
Zones 2-4 as a single layout. Each zone is a component imported from
mfip/dashboard/zones/, not a separately routed page. See the
2026-05-13 routing architecture decision in decisions.md.

Importing this module triggers two side effects:
  1. dash.register_page registers the /analysis route.
  2. Importing zone1 transitively loads zone1's @callback decorators,
     registering its callbacks with the global callback map.
"""

from __future__ import annotations

import dash
from dash import html

from mfip.dashboard.zones import zone1

layout = html.Div(
    [
        zone1.layout,
        html.Div(id="zone-2", className="zone-placeholder"),
        html.Div(id="zone-3", className="zone-placeholder"),
        html.Div(id="zone-4", className="zone-placeholder"),
    ],
    id="analysis-page",
)

dash.register_page(
    __name__,
    path="/analysis",
    layout=layout,
    name="Analysis",
)
