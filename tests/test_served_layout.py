"""
Smoke test: every registered callback's Input/Output/State IDs resolve
against either the served app shell layout or some registered page's
layout.

Catches the Dash 3.x failure mode where a callback references an ID
that exists in a Python module's layout constant but is not actually
mounted in the served DOM at app boot. With
suppress_callback_exceptions=True (which app.py sets), this fails
silently at boot and only surfaces in the browser dev panel.

See ideas.md 2026-05-12 IDEA-023 for full rationale and the 2026-05-13
routing architecture entry in decisions.md for the three-strikes
pattern that motivated graduating the idea.
"""

from __future__ import annotations

import dash
import pytest

from mfip.dashboard.app import app
from dash._callback import GLOBAL_CALLBACK_MAP


def _collect_ids_from_component(component, collected: set[str]) -> None:
    """Recursively walk a Dash component tree, adding every string id to collected.

    Components without an id attribute (strings, numbers, None) and components
    whose id is a dict (pattern-matching) are silently skipped — pattern-
    matching IDs are handled at the callback-side instead.
    """
    if component is None:
        return
    if not hasattr(component, "children") and not hasattr(component, "id"):
        return

    component_id = getattr(component, "id", None)
    if isinstance(component_id, str):
        collected.add(component_id)

    children = getattr(component, "children", None)
    if children is None:
        return
    if isinstance(children, (list, tuple)):
        for child in children:
            _collect_ids_from_component(child, collected)
    else:
        _collect_ids_from_component(children, collected)


def _collect_served_layout_ids(app) -> set[str]:
    """IDs reachable from the app shell layout (no page contents)."""
    collected: set[str] = set()
    layout = app.layout() if callable(app.layout) else app.layout
    _collect_ids_from_component(layout, collected)
    return collected


def _collect_page_registry_ids() -> set[str]:
    """IDs reachable from every layout registered via dash.register_page."""
    collected: set[str] = set()
    for entry in dash.page_registry.values():
        page_layout = entry.get("layout")
        if callable(page_layout):
            page_layout = page_layout()
        _collect_ids_from_component(page_layout, collected)
    return collected


def _dep_component_id(dep):
    """Return the component_id of a callback dependency.

    Dash 3.x callback_map entries store inputs/state as dicts with an
    'id' key, and output as either a single Output object (with
    .component_id) or a list of Output objects.
    """
    if isinstance(dep, dict):
        return dep.get("id")
    return getattr(dep, "component_id", None)


def test_all_callback_ids_resolve():
    """Every callback's Input/Output/State IDs resolve against served
    layout or some registered page layout."""
    resolvable = _collect_served_layout_ids(app) | _collect_page_registry_ids()

    unresolved: list[tuple[str, str, str]] = []
    pattern_matching_skipped: list[tuple[str, str, dict]] = []

    for callback_key, spec in GLOBAL_CALLBACK_MAP.items():
        # Normalise output to a list — single-output specs store one
        # Output object directly; multi-output specs store a list.
        output = spec.get("output")
        if output is None:
            outputs = []
        elif isinstance(output, list):
            outputs = output
        else:
            outputs = [output]

        sources = (
            ("inputs", spec.get("inputs") or []),
            ("state", spec.get("state") or []),
            ("output", outputs),
        )

        for dep_type, deps in sources:
            for dep in deps:
                cid = _dep_component_id(dep)
                if cid is None:
                    continue
                if isinstance(cid, dict):
                    pattern_matching_skipped.append((callback_key, dep_type, cid))
                    continue
                if cid not in resolvable:
                    unresolved.append((callback_key, dep_type, cid))

    if pattern_matching_skipped:
        print(
            f"\n[INFO] Skipped {len(pattern_matching_skipped)} pattern-matching "
            f"dependencies (dict component_ids):"
        )
        for cb, dep_type, cid in pattern_matching_skipped:
            print(f"  callback={cb} {dep_type}={cid}")

    if unresolved:
        msg_lines = [
            f"{len(unresolved)} callback dependency ID(s) do not resolve "
            f"against the served layout or any registered page:"
        ]
        for cb, dep_type, cid in unresolved:
            msg_lines.append(f"  callback={cb} {dep_type}={cid!r}")
        msg_lines.append("")
        msg_lines.append(
            "Resolvable IDs collected from served layout + page registry:"
        )
        msg_lines.append(f"  {sorted(resolvable)}")
        pytest.fail("\n".join(msg_lines))
