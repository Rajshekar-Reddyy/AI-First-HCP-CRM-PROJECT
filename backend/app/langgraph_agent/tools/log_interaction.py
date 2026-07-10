import logging
from typing import Any

from pydantic import ValidationError
from datetime import date

from app.langgraph_agent.prompts import ENTITY_EXTRACTION_PROMPT
from app.langgraph_agent.schemas import ExtractedInteractionPayload
from app.langgraph_agent.tools.context import ToolContext
from app.schemas.interaction import InteractionCreate, InteractionRead


logger = logging.getLogger(__name__)


async def log_interaction(context: ToolContext, arguments: dict[str, Any], user_message: str) -> dict[str, Any]:
    """Extract a complete interaction from natural language and persist it."""

    extraction = await context.ai.complete_model(
        [
            {"role": "system", "content": ENTITY_EXTRACTION_PROMPT},
            {"role": "user", "content": user_message},
        ],
        ExtractedInteractionPayload,
    )

    print("========== AI EXTRACTION ==========")
    print(extraction.model_dump(mode="json"))
    print("===================================")
    try:
        from datetime import date, timedelta

        data = extraction.model_dump()
        message = user_message.lower()

        if "today" in message:
            data["interaction_date"] = date.today().isoformat()
        elif "yesterday" in message:
            data["interaction_date"] = (date.today() - timedelta(days=1)).isoformat()
        elif "tomorrow" in message:
            data["interaction_date"] = (date.today() + timedelta(days=1)).isoformat()

        payload = InteractionCreate(**data)
    except ValidationError as exc:
        logger.warning("Interaction extraction failed validation", extra={"session_id": context.session_id, "errors": exc.errors()})
        return context.validation_error("Unable to validate extracted interaction.", exc)

    logger.info(
        "Persisting extracted interaction",
        extra={"session_id": context.session_id, "hcp_name": payload.hcp_name, "extracted_entities": extraction.model_dump(mode="json")},
    )
    interaction = context.repository.create_interaction(payload)
    data = InteractionRead.model_validate(interaction).model_dump(mode="json")
    return {"interaction": data, "message": f"Logged interaction with {interaction.hcp.name}.", "extracted_entities": extraction.model_dump(mode="json")}
