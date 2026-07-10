from datetime import datetime
from typing import Any
import logging

from dateutil import parser

from app.langgraph_agent.schemas import ReminderArguments
from app.langgraph_agent.tools.context import ToolContext
from app.schemas.reminder import ReminderCreate, ReminderRead


logger = logging.getLogger(__name__)


async def schedule_reminder(context: ToolContext, arguments: dict[str, Any], user_message: str) -> dict[str, Any]:
    """Create a follow-up reminder tied to an HCP and active interaction when available."""

    parsed = ReminderArguments(**arguments)
    interaction_id = parsed.interaction_id or context.latest_interaction_id()
    hcp_id = parsed.hcp_id
    if not hcp_id and interaction_id:
        hcp_id = context.repository.get_interaction(int(interaction_id)).hcp_id
    if not hcp_id:
        return {"error": "A reminder needs an HCP or an active interaction."}

    due_value = parsed.due_at or parsed.date or parsed.when
    due_at = parser.parse(str(due_value), fuzzy=True) if due_value else datetime.now().replace(hour=9, minute=0, second=0, microsecond=0)
    title = parsed.title or parsed.follow_up or "Follow up with HCP"
    reminder = context.repository.create_reminder(
        ReminderCreate(
            hcp_id=int(hcp_id),
            interaction_id=int(interaction_id) if interaction_id else None,
            title=title,
            due_at=due_at,
            notes=parsed.notes,
        )
    )
    logger.info(
        "Created reminder",
        extra={"session_id": context.session_id, "reminder_id": reminder.id, "hcp_id": reminder.hcp_id, "interaction_id": reminder.interaction_id},
    )
    return {"reminder": ReminderRead.model_validate(reminder).model_dump(mode="json"), "message": "Reminder scheduled."}
