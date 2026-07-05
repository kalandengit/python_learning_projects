"""ICS (RFC 5545) calendar feed generation from a user's published shifts."""

from __future__ import annotations

from datetime import datetime, timezone

from ..models import Shift

_ICS_DT = "%Y%m%dT%H%M%SZ"


def _fmt(dt: datetime) -> str:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).strftime(_ICS_DT)


def _escape(text: str) -> str:
    # RFC 5545 text escaping.
    return (
        text.replace("\\", "\\\\")
        .replace(";", "\\;")
        .replace(",", "\\,")
        .replace("\n", "\\n")
    )


def render_calendar(shifts: list[Shift], *, calendar_name: str = "StaffHub") -> str:
    """Return an ICS document for the given shifts. CRLF line endings per spec."""
    now = _fmt(datetime.now(timezone.utc))
    lines: list[str] = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//StaffHub//Shift Planner//EN",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        f"X-WR-CALNAME:{_escape(calendar_name)}",
    ]
    for shift in shifts:
        lines += [
            "BEGIN:VEVENT",
            f"UID:{shift.id}@staffhub",
            f"DTSTAMP:{now}",
            f"DTSTART:{_fmt(shift.starts_at)}",
            f"DTEND:{_fmt(shift.ends_at)}",
            f"SUMMARY:{_escape(shift.title)}",
        ]
        if shift.location:
            lines.append(f"LOCATION:{_escape(shift.location)}")
        lines.append("END:VEVENT")
    lines.append("END:VCALENDAR")
    return "\r\n".join(lines) + "\r\n"
