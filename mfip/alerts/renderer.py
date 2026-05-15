"""Multipart MIME rendering for `Alert` payloads.

`render_alert(alert) -> EmailMessage` returns a multipart/alternative
message with a `text/plain` part and a `text/html` part. The HTML
part uses inline styles only — many email clients strip `<style>`
blocks. The self-contained-alerts principle (see `06_SECURITY_COUNCIL.docx`)
requires that the body be enough to debug without external links.

Locked implementation choices (see `decisions.md` 2026-05-15
"mfip_alerts implementation choices"):

- Subject: ``[MFIP {severity}] {title}``
- Severity colours: Critical = ``#c0392b``, Warning = ``#e67e22``,
  Advisory = ``#f1c40f``
- Stack trace truncated to 30 lines, then ``... [truncated]``
"""

from __future__ import annotations

import html
from email.message import EmailMessage

from mfip.alerts.models import Alert

SEVERITY_COLOR: dict[str, str] = {
    "Critical": "#c0392b",
    "Warning": "#e67e22",
    "Advisory": "#f1c40f",
}

STACK_TRACE_MAX_LINES = 30
TRUNCATION_MARKER = "... [truncated]"


def _truncate_stack(stack: str | None) -> str | None:
    if stack is None:
        return None
    lines = stack.splitlines()
    if len(lines) <= STACK_TRACE_MAX_LINES:
        return "\n".join(lines)
    kept = lines[:STACK_TRACE_MAX_LINES]
    kept.append(TRUNCATION_MARKER)
    return "\n".join(kept)


def _format_timestamp(alert: Alert) -> str:
    return alert.timestamp.strftime("%Y-%m-%d %H:%M:%S %Z").strip()


def _build_plain_body(alert: Alert) -> str:
    parts: list[str] = []
    parts.append(f"[{alert.severity}] {alert.title}")
    parts.append(f"Time: {_format_timestamp(alert)}")
    parts.append(f"Issuing agent: {alert.issuing_agent}")
    if alert.correlation_id:
        parts.append(f"Correlation ID: {alert.correlation_id}")
    parts.append("")
    parts.append("Summary:")
    parts.append(alert.summary)

    if alert.error_class or alert.error_message or alert.stack_trace:
        parts.append("")
        parts.append("Error:")
        if alert.error_class:
            parts.append(f"  class: {alert.error_class}")
        if alert.error_message:
            parts.append(f"  message: {alert.error_message}")
        truncated = _truncate_stack(alert.stack_trace)
        if truncated:
            parts.append("  stack trace:")
            for line in truncated.splitlines():
                parts.append(f"    {line}")

    if alert.context_fields:
        parts.append("")
        parts.append("Context:")
        for key, value in alert.context_fields.items():
            parts.append(f"  {key}: {value}")

    parts.append("")
    parts.append("Recommended action:")
    parts.append(alert.recommended_action)

    if alert.dashboard_link:
        parts.append("")
        parts.append(f"Dashboard: {alert.dashboard_link}")

    return "\n".join(parts) + "\n"


def _build_html_body(alert: Alert) -> str:
    color = SEVERITY_COLOR[alert.severity]
    e = html.escape

    sections: list[str] = []
    sections.append(
        f'<div style="background:{color};color:#ffffff;padding:12px 16px;'
        f'font-family:Arial,sans-serif;font-size:16px;font-weight:bold;">'
        f"[{e(alert.severity)}] {e(alert.title)}"
        f"</div>"
    )
    body_open = (
        '<div style="font-family:Arial,sans-serif;font-size:14px;'
        'color:#222222;padding:16px;">'
    )
    sections.append(body_open)

    meta_lines: list[str] = []
    meta_lines.append(
        f'<div><strong>Time:</strong> {e(_format_timestamp(alert))}</div>'
    )
    meta_lines.append(
        f'<div><strong>Issuing agent:</strong> {e(alert.issuing_agent)}</div>'
    )
    if alert.correlation_id:
        meta_lines.append(
            f'<div><strong>Correlation ID:</strong> '
            f'{e(alert.correlation_id)}</div>'
        )
    sections.append("".join(meta_lines))

    sections.append(
        '<p style="margin-top:12px;"><strong>Summary</strong></p>'
        f'<p style="margin:4px 0 0 0;">{e(alert.summary)}</p>'
    )

    if alert.error_class or alert.error_message or alert.stack_trace:
        sections.append('<p style="margin-top:12px;"><strong>Error</strong></p>')
        if alert.error_class:
            sections.append(
                f'<div><strong>class:</strong> {e(alert.error_class)}</div>'
            )
        if alert.error_message:
            sections.append(
                f'<div><strong>message:</strong> {e(alert.error_message)}</div>'
            )
        truncated = _truncate_stack(alert.stack_trace)
        if truncated:
            sections.append(
                '<pre style="background:#f4f4f4;border:1px solid #dddddd;'
                'padding:8px;font-family:Consolas,Menlo,monospace;'
                'font-size:12px;overflow:auto;">'
                f"<code>{e(truncated)}</code></pre>"
            )

    if alert.context_fields:
        sections.append('<p style="margin-top:12px;"><strong>Context</strong></p>')
        dl_parts = ['<dl style="margin:4px 0 0 0;">']
        for key, value in alert.context_fields.items():
            dl_parts.append(
                f'<dt style="font-weight:bold;">{e(key)}</dt>'
                f'<dd style="margin:0 0 4px 16px;">{e(value)}</dd>'
            )
        dl_parts.append("</dl>")
        sections.append("".join(dl_parts))

    sections.append(
        '<p style="margin-top:12px;"><strong>Recommended action</strong></p>'
        f'<p style="margin:4px 0 0 0;">{e(alert.recommended_action)}</p>'
    )

    if alert.dashboard_link:
        sections.append(
            f'<p style="margin-top:12px;"><a href="{e(alert.dashboard_link)}" '
            f'style="color:{color};">Open in MFIP dashboard</a></p>'
        )

    sections.append("</div>")
    return "<!doctype html><html><body>" + "".join(sections) + "</body></html>"


def render_alert(alert: Alert) -> EmailMessage:
    """Render the alert to a multipart/alternative EmailMessage.

    Subject and body content are derived from the alert; From/To
    headers are set by `send_alert` once the SMTP credentials are
    known (the renderer is intentionally credential-free).
    """
    msg = EmailMessage()
    msg["Subject"] = f"[MFIP {alert.severity}] {alert.title}"
    msg.set_content(_build_plain_body(alert))
    msg.add_alternative(_build_html_body(alert), subtype="html")
    return msg
