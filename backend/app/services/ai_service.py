"""
app/services/ai_service.py

Fetches incident timeline from the database and streams
an LLM-generated plain-English summary via OpenAI.
"""

from __future__ import annotations

import json
from collections.abc import AsyncGenerator
from datetime import datetime, timezone

from openai import AsyncOpenAI
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.audit_log import AuditLog
from app.models.incident import Incident

# ---------------------------------------------------------------------------
# OpenAI client — reads OPENAI_API_KEY from environment automatically
# ---------------------------------------------------------------------------

_client = AsyncOpenAI()  # uses OPENAI_API_KEY env var


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _fmt(dt: datetime | None) -> str:
    """Format a datetime as a readable UTC string, or 'N/A'."""
    if dt is None:
        return "N/A"
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")


def _duration(start: datetime | None, end: datetime | None) -> str:
    """Return human-readable duration between two datetimes."""
    if start is None or end is None:
        return "N/A"
    delta = end - start
    total = int(delta.total_seconds())
    if total < 60:
        return f"{total}s"
    if total < 3600:
        return f"{total // 60}m {total % 60}s"
    return f"{total // 3600}h {(total % 3600) // 60}m"


def _build_prompt(incident: Incident, audit_logs: list[AuditLog]) -> str:
    """
    Build a structured prompt from the incident timeline.
    The richer the data, the better the summary.
    """

    # ── Incident header ────────────────────────────────────────────────────
    sla_status = "BREACHED" if incident.sla_breached else "within SLA"
    time_to_ack = _duration(incident.created_at, incident.acknowledged_at)
    time_to_resolve = _duration(incident.created_at, incident.resolved_at)

    header = f"""INCIDENT SUMMARY REQUEST
========================
ID:            #{incident.id}
Title:         {incident.title}
Priority:      {incident.priority.value}
Status:        {incident.status.value}
SLA Status:    {sla_status}
SLA Deadline:  {_fmt(incident.sla_deadline)}
Created At:    {_fmt(incident.created_at)}
Acknowledged:  {_fmt(incident.acknowledged_at)} (time to ack: {time_to_ack})
Resolved:      {_fmt(incident.resolved_at)} (time to resolve: {time_to_resolve})
"""

    # ── Alerts ────────────────────────────────────────────────────────────
    alert_lines = []
    for a in incident.alerts:
        labels_str = json.dumps(a.labels, separators=(",", ":")) if a.labels else "{}"
        alert_lines.append(
            f"  - [{_fmt(a.created_at)}] {a.source}/{a.name} on {a.service_name}"
            + (f" | {a.message}" if a.message else "")
            + f" | labels: {labels_str}"
        )

    alerts_section = "ALERTS INGESTED ({} total):\n".format(len(incident.alerts))
    alerts_section += "\n".join(alert_lines) if alert_lines else "  (none)"

    # ── Audit log ─────────────────────────────────────────────────────────
    audit_lines = []
    for log in audit_logs:
        audit_lines.append(
            f"  [{_fmt(log.created_at)}] {log.actor} — {log.event}"
            + (f": {log.detail}" if hasattr(log, "detail") and log.detail else "")
        )

    audit_section = "TIMELINE / AUDIT LOG ({} events):\n".format(len(audit_logs))
    audit_section += "\n".join(audit_lines) if audit_lines else "  (no audit events)"

    # ── Full prompt ───────────────────────────────────────────────────────
    return f"{header}\n{alerts_section}\n\n{audit_section}"


# ---------------------------------------------------------------------------
# System prompt — defines the AI's persona and output format
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """You are an expert Site Reliability Engineer assistant embedded in an incident management platform.

Your job is to generate clear, concise incident summaries for on-call engineers.

Given structured incident data (alerts, timeline, SLA info), produce a summary with these sections:

**What happened**
One or two sentences describing the incident — what service was affected, what kind of failure occurred, and when.

**Timeline**
A brief chronological summary of key events — when the alert fired, when it was acknowledged, escalations, resolution.

**Impact**
Priority level, SLA status (was it breached?), duration of the incident.

**What to check next** (if still open)
2–3 specific, actionable suggestions based on the alert type and service involved.

Rules:
- Be direct and specific — no filler phrases like "It appears that" or "It seems like"
- Use the actual service names, alert names, and timestamps from the data
- If the incident is resolved, skip the "What to check next" section
- Keep the entire summary under 300 words
- Use plain language an on-call engineer can act on immediately"""


# ---------------------------------------------------------------------------
# Main streaming function
# ---------------------------------------------------------------------------


async def stream_incident_summary(
    db: AsyncSession,
    incident_id: int,
    team_id: int,
) -> AsyncGenerator[str, None]:
    """
    Fetch incident with full timeline and stream an AI-generated summary.

    Yields SSE-formatted strings:  data: <chunk>\n\n
    Yields a final:                data: [DONE]\n\n
    """

    # ── Fetch incident with relationships eagerly loaded ──────────────────
    result = await db.execute(
        select(Incident)
        .where(Incident.id == incident_id, Incident.team_id == team_id)
        .options(
            selectinload(Incident.alerts),
            selectinload(Incident.audit_logs),
            selectinload(Incident.sla_policy),
        )
    )
    incident = result.scalar_one_or_none()

    if incident is None:
        yield "data: Incident not found or you do not have access to it.\n\n"
        yield "data: [DONE]\n\n"
        return

    # ── Fetch audit logs ordered by time ─────────────────────────────────
    audit_result = await db.execute(
        select(AuditLog)
        .where(AuditLog.incident_id == incident_id)
        .order_by(AuditLog.created_at)
    )
    audit_logs = audit_result.scalars().all()

    # ── Build prompt ──────────────────────────────────────────────────────
    user_prompt = _build_prompt(incident, list(audit_logs))

    # ── Stream from OpenAI ────────────────────────────────────────────────
    try:
        stream = await _client.chat.completions.create(
            model="gpt-4o-mini",  # fast + cheap, perfect for summaries
            max_tokens=600,
            temperature=0.3,  # low temp = consistent, factual output
            stream=True,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
        )

        async for chunk in stream:
            delta = chunk.choices[0].delta
            if delta and delta.content:
                # SSE format — each chunk on its own data: line
                yield f"data: {delta.content}\n\n"

    except Exception as e:
        yield f"data: Error generating summary: {str(e)}\n\n"

    finally:
        yield "data: [DONE]\n\n"
