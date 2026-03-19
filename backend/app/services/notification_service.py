import logging

import httpx
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.notification_config import NotificationConfig

logger = logging.getLogger(__name__)

# Slack color codes
COLORS = {
    "P1": "#FF0000",  # red
    "P2": "#FF6600",  # orange
    "P3": "#FFA500",  # yellow
    "P4": "#36A64F",  # green
}


async def _get_active_configs(
    db: AsyncSession,
    team_id: int,
    event_type: str,
) -> list[NotificationConfig]:
    """Get active notification configs for this team and event type."""
    filters = [
        NotificationConfig.team_id == team_id,
        NotificationConfig.is_active == True,  # noqa: E712
    ]

    if event_type == "new_incident":
        filters.append(NotificationConfig.notify_on_new_incident == True)  # noqa: E712
    elif event_type == "sla_warning":
        filters.append(NotificationConfig.notify_on_sla_warning == True)  # noqa: E712
    elif event_type == "escalation":
        filters.append(NotificationConfig.notify_on_escalation == True)  # noqa: E712

    result = await db.execute(select(NotificationConfig).where(and_(*filters)))
    return list(result.scalars().all())


async def _send_slack(webhook_url: str, payload: dict) -> bool:
    """Send a POST request to a Slack webhook URL."""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.post(webhook_url, json=payload)
            if response.status_code == 200:
                return True
            logger.warning(f"Slack webhook returned {response.status_code}")
            return False
    except Exception as e:
        logger.error(f"Slack notification failed: {e}")
        return False


async def notify_new_incident(
    db: AsyncSession,
    team_id: int,
    incident_id: int,
    title: str,
    priority: str,
    service_name: str,
) -> None:
    """Send Slack notification when a new incident is created."""
    configs = await _get_active_configs(db, team_id, "new_incident")
    if not configs:
        return

    color = COLORS.get(priority, "#808080")

    payload = {
        "attachments": [
            {
                "color": color,
                "blocks": [
                    {
                        "type": "header",
                        "text": {
                            "type": "plain_text",
                            "text": f"🚨 New Incident — {priority}",
                        },
                    },
                    {
                        "type": "section",
                        "fields": [
                            {
                                "type": "mrkdwn",
                                "text": f"*Incident:*\n#{incident_id} — {title}",
                            },
                            {"type": "mrkdwn", "text": f"*Service:*\n{service_name}"},
                            {"type": "mrkdwn", "text": f"*Priority:*\n{priority}"},
                            {"type": "mrkdwn", "text": "*Status:*\nTriggered"},
                        ],
                    },
                    {
                        "type": "actions",
                        "elements": [
                            {
                                "type": "button",
                                "text": {"type": "plain_text", "text": "View Incident"},
                                "url": f"http://localhost:3000/incidents/{incident_id}",
                                "style": "danger",
                            }
                        ],
                    },
                ],
            }
        ]
    }

    for config in configs:
        sent = await _send_slack(config.webhook_url, payload)
        logger.info(
            f"Slack notification (new_incident #{incident_id}) "
            f"to '{config.name}': {'sent' if sent else 'failed'}"
        )


async def notify_sla_warning(
    db: AsyncSession,
    team_id: int,
    incident_id: int,
    title: str,
    priority: str,
    minutes_remaining: int,
) -> None:
    """Send Slack notification when SLA is about to breach."""
    configs = await _get_active_configs(db, team_id, "sla_warning")
    if not configs:
        return

    payload = {
        "attachments": [
            {
                "color": "#FFA500",
                "blocks": [
                    {
                        "type": "header",
                        "text": {
                            "type": "plain_text",
                            "text": f"⚠️ SLA Warning — {minutes_remaining} minutes remaining",
                        },
                    },
                    {
                        "type": "section",
                        "fields": [
                            {
                                "type": "mrkdwn",
                                "text": f"*Incident:*\n#{incident_id} — {title}",
                            },
                            {"type": "mrkdwn", "text": f"*Priority:*\n{priority}"},
                            {
                                "type": "mrkdwn",
                                "text": f"*SLA breaches in:*\n{minutes_remaining} minutes",
                            },
                            {
                                "type": "mrkdwn",
                                "text": "*Action needed:*\nResolve this incident now",
                            },
                        ],
                    },
                    {
                        "type": "actions",
                        "elements": [
                            {
                                "type": "button",
                                "text": {"type": "plain_text", "text": "View Incident"},
                                "url": f"http://localhost:3000/incidents/{incident_id}",
                                "style": "primary",
                            }
                        ],
                    },
                ],
            }
        ]
    }

    for config in configs:
        sent = await _send_slack(config.webhook_url, payload)
        logger.info(
            f"Slack notification (sla_warning #{incident_id}) "
            f"to '{config.name}': {'sent' if sent else 'failed'}"
        )


async def notify_escalation(
    db: AsyncSession,
    team_id: int,
    incident_id: int,
    title: str,
    priority: str,
    step_order: int,
    notify_target: str,
) -> None:
    """Send Slack notification when an incident is escalated."""
    configs = await _get_active_configs(db, team_id, "escalation")
    if not configs:
        return

    payload = {
        "attachments": [
            {
                "color": "#FF6600",
                "blocks": [
                    {
                        "type": "header",
                        "text": {
                            "type": "plain_text",
                            "text": f"📢 Incident Escalated — Step {step_order}",
                        },
                    },
                    {
                        "type": "section",
                        "fields": [
                            {
                                "type": "mrkdwn",
                                "text": f"*Incident:*\n#{incident_id} — {title}",
                            },
                            {"type": "mrkdwn", "text": f"*Priority:*\n{priority}"},
                            {
                                "type": "mrkdwn",
                                "text": f"*Escalated to:*\n{notify_target}",
                            },
                            {
                                "type": "mrkdwn",
                                "text": f"*Escalation step:*\n{step_order}",
                            },
                        ],
                    },
                    {
                        "type": "actions",
                        "elements": [
                            {
                                "type": "button",
                                "text": {
                                    "type": "plain_text",
                                    "text": "Acknowledge Now",
                                },
                                "url": f"http://localhost:3000/incidents/{incident_id}",
                                "style": "danger",
                            }
                        ],
                    },
                ],
            }
        ]
    }

    for config in configs:
        sent = await _send_slack(config.webhook_url, payload)
        logger.info(
            f"Slack notification (escalation #{incident_id} step {step_order}) "
            f"to '{config.name}': {'sent' if sent else 'failed'}"
        )
