"""Compose and send the daily change-summary email."""
from __future__ import annotations
import os
import smtplib
from email.message import EmailMessage
from .diff import HoldingsDiff


def _format_diff_html(d: HoldingsDiff) -> str:
    if not d.has_changes:
        return f"<h3>{d.ticker}</h3><p><em>No material changes.</em></p>"

    parts = [
        f"<h3>{d.ticker} &mdash; {d.as_of_today} vs {d.as_of_previous}</h3>"
    ]

    if d.added:
        rows = "".join(
            f"<tr><td>{x['ticker']}</td><td>{x['name']}</td>"
            f"<td style='text-align:right'>{x['weight']:.2f}%</td></tr>"
            for x in d.added
        )
        parts.append(
            "<p><b>New positions</b></p>"
            "<table border='1' cellpadding='4' cellspacing='0'>"
            "<tr><th>Symbol</th><th>Name</th><th>Weight</th></tr>"
            f"{rows}</table>"
        )

    if d.removed:
        rows = "".join(
            f"<tr><td>{x['ticker']}</td><td>{x['name']}</td>"
            f"<td style='text-align:right'>{x['weight']:.2f}%</td></tr>"
            for x in d.removed
        )
        parts.append(
            "<p><b>Removed positions</b></p>"
            "<table border='1' cellpadding='4' cellspacing='0'>"
            "<tr><th>Symbol</th><th>Name</th><th>Prev Weight</th></tr>"
            f"{rows}</table>"
        )

    if d.changed:
        rows = "".join(
            f"<tr><td>{x['ticker']}</td><td>{x['name']}</td>"
            f"<td style='text-align:right'>{x['previous']:.2f}%</td>"
            f"<td style='text-align:right'>{x['current']:.2f}%</td>"
            f"<td style='text-align:right'>{x['delta']:+.2f}%</td></tr>"
            for x in d.changed
        )
        parts.append(
            "<p><b>Weight changes (&ge; 0.25%)</b></p>"
            "<table border='1' cellpadding='4' cellspacing='0'>"
            "<tr><th>Symbol</th><th>Name</th><th>Prev</th><th>Now</th><th>&Delta;</th></tr>"
            f"{rows}</table>"
        )

    return "\n".join(parts)


def send_email(diffs: list[HoldingsDiff]) -> None:
    host = os.environ["SMTP_HOST"]
    port = int(os.environ.get("SMTP_PORT", "587"))
    user = os.environ["SMTP_USER"]
    password = os.environ["SMTP_PASSWORD"]
    sender = os.environ.get("EMAIL_FROM", user)
    recipient = os.environ["EMAIL_TO"]

    any_changes = any(d.has_changes for d in diffs)
    subject_prefix = "[Unlimited ETFs]" if any_changes else "[Unlimited ETFs] no changes"
    summary = ", ".join(
        f"{d.ticker}: {len(d.added)}+/{len(d.removed)}-/{len(d.changed)}~" for d in diffs
    )

    body_html = (
        "<p>Daily holdings comparison vs previous snapshot.</p>"
        f"<p><b>Summary:</b> {summary}</p>"
        + "\n".join(_format_diff_html(d) for d in diffs)
    )

    msg = EmailMessage()
    msg["Subject"] = f"{subject_prefix} {summary}"
    msg["From"] = sender
    msg["To"] = recipient
    msg.set_content("HTML email — please use a client that renders HTML.")
    msg.add_alternative(body_html, subtype="html")

    with smtplib.SMTP(host, port) as s:
        s.starttls()
        s.login(user, password)
        s.send_message(msg)
