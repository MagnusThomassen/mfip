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


def _zone_placeholder(zone_id: str, title: str) -> html.Div:
    return html.Div(
        [
            html.Div(title, className="zone-placeholder-title"),
            html.Div("Phase 1 placeholder",
                     className="zone-placeholder-caption"),
        ],
        id=zone_id,
        className="zone-placeholder",
    )


layout = html.Div(
    [
        zone1.layout,
        html.Div(
            [
                _zone_placeholder("zone-2", "Zone 2 — Company Deep Dive"),
                _zone_placeholder("zone-3", "Zone 3 — Intelligence Feed"),
                _zone_placeholder("zone-4", "Zone 4 — Portfolio View"),
            ],
            id="analysis-body",
            className="analysis-grid",
        ),
    ],
    id="analysis-page",
)

dash.register_page(
    __name__,
    path="/analysis",
    layout=layout,
    name="Analysis",
)
