from typing import Any
import logging

from app.langgraph_agent.prompts import MEETING_SUMMARY_PROMPT
from app.langgraph_agent.schemas import SummaryResponse
from app.langgraph_agent.tools.context import ToolContext
from app.schemas.interaction import InteractionRead, InteractionUpdate


logger = logging.getLogger(__name__)


async def generate_meeting_summary(context: ToolContext, arguments: dict[str, Any], user_message: str) -> dict[str, Any]:
    """Generate and store a professional meeting summary."""

    interaction_id = context.require_interaction_id(arguments.get("interaction_id"))
    interaction = context.repository.get_interaction(interaction_id)
    source = InteractionRead.model_validate(interaction).model_dump(mode="json")
    summary = await context.ai.complete_model(
        [
            {"role": "system", "content": MEETING_SUMMARY_PROMPT},
            {"role": "user", "content": str(source)},
        ],
        SummaryResponse,
    )
    updated = context.repository.update_interaction(
        interaction_id,
        InteractionUpdate(summary=summary.summary, voice_summary=summary.summary),
    )
    logger.info("Stored generated meeting summary", extra={"session_id": context.session_id, "interaction_id": interaction_id})
    return {"interaction": InteractionRead.model_validate(updated).model_dump(mode="json"), "summary": summary.summary}
