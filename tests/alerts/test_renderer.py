"""Renderer tests for `mfip.alerts.renderer.render_alert`."""

from __future__ import annotations

import pytest

from mfip.alerts.models import Alert
from mfip.alerts.renderer import SEVERITY_COLOR, render_alert


def _alert(**overrides) -> Alert:
    defaults = dict(
        severity="Critical",
        issuing_agent="security_council",
        title="Bloomberg ingestion failure",
        summary="EOD ingestion did not complete for EQNR.",
        recommended_action="Re-run ingestion from the lab notebook.",
    )
    defaults.update(overrides)
    return Alert(**defaults)


@pytest.mark.parametrize("severity", ["Critical", "Warning", "Advisory"])
def test_subject_line_format(severity):
    alert = _alert(severity=severity, title="Test title")
    msg = render_alert(alert)
    assert msg["Subject"] == f"[MFIP {severity}] Test title"


def test_message_is_multipart_alternative_with_both_parts():
    msg = render_alert(_alert())

    assert msg.is_multipart()
    assert msg.get_content_type() == "multipart/alternative"

    plain = msg.get_body(preferencelist=("plain",))
    html = msg.get_body(preferencelist=("html",))
    assert plain is not None and plain.get_content_type() == "text/plain"
    assert html is not None and html.get_content_type() == "text/html"


@pytest.mark.parametrize(
    "severity,color",
    [
        ("Critical", SEVERITY_COLOR["Critical"]),
        ("Warning", SEVERITY_COLOR["Warning"]),
        ("Advisory", SEVERITY_COLOR["Advisory"]),
    ],
)
def test_html_body_contains_severity_color(severity, color):
    msg = render_alert(_alert(severity=severity))
    html_part = msg.get_body(preferencelist=("html",))
    body = html_part.get_content()
    assert color in body
    # The locked colors are mutually exclusive — no off-severity color
    # should leak in.
    for other_sev, other_color in SEVERITY_COLOR.items():
        if other_sev == severity:
            continue
        assert other_color not in body


def test_stack_trace_truncated_to_thirty_lines_with_marker():
    fifty_lines = "\n".join(f"frame {i}" for i in range(50))
    msg = render_alert(_alert(stack_trace=fifty_lines))

    plain = msg.get_body(preferencelist=("plain",)).get_content()
    html = msg.get_body(preferencelist=("html",)).get_content()

    assert "... [truncated]" in plain
    assert "... [truncated]" in html

    # The HTML stack section lives inside the <pre><code> block.
    start = html.index("<pre")
    end = html.index("</pre>", start)
    pre_block = html[start:end]
    code_start = pre_block.index("<code>") + len("<code>")
    code_end = pre_block.index("</code>", code_start)
    stack_text = pre_block[code_start:code_end]
    stack_lines = stack_text.splitlines()
    # 30 content lines + 1 truncation marker = 31 lines max.
    assert len(stack_lines) <= 31
    assert stack_lines[-1] == "... [truncated]"


def test_context_fields_rendered_in_both_formats_and_empty_does_not_break():
    # Non-empty.
    alert = _alert(context_fields={"ticker": "EQNR", "session": "15"})
    msg = render_alert(alert)
    plain = msg.get_body(preferencelist=("plain",)).get_content()
    html = msg.get_body(preferencelist=("html",)).get_content()

    assert "ticker: EQNR" in plain
    assert "session: 15" in plain

    assert "<dl" in html
    assert "<dt" in html and "ticker" in html and "EQNR" in html
    assert "</dl>" in html

    # Empty context_fields renders without raising and without a <dl> block.
    msg_empty = render_alert(_alert())
    html_empty = msg_empty.get_body(preferencelist=("html",)).get_content()
    plain_empty = msg_empty.get_body(preferencelist=("plain",)).get_content()
    assert "<dl" not in html_empty
    # Plain text still includes severity header and recommended action.
    assert "Recommended action:" in plain_empty
