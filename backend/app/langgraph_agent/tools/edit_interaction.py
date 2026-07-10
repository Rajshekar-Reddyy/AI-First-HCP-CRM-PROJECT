import logging
from typing import Any

from pydantic import ValidationError

from app.langgraph_agent.prompts import ENTITY_UPDATE_PROMPT
from app.langgraph_agent.schemas import InteractionPatchPayload
from app.langgraph_agent.tools.context import ToolContext
from app.schemas.interaction import InteractionRead, InteractionUpdate


logger = logging.getLogger(__name__)


async def edit_interaction(context: ToolContext, arguments: dict[str, Any], user_message: str) -> dict[str, Any]:
    """Update only explicitly requested fields on the active interaction."""

    interaction_id = context.require_interaction_id(arguments.get("interaction_id"))
    raw_patch = {key: value for key, value in arguments.items() if key in InteractionPatchPayload.model_fields and value is not None}
    if not raw_patch:
        patch = await context.ai.complete_model(
            [
                {"role": "system", "content": ENTITY_UPDATE_PROMPT},
                {"role": "user", "content": user_message},
            ],
            InteractionPatchPayload,
        )
    else:
        patch = InteractionPatchPayload(**raw_patch)

    clean_patch = patch.model_dump(exclude_unset=True, exclude_none=True)
    if not clean_patch:
        return {"error": "No valid interaction fields were identified for update."}
    try:
        update = InteractionUpdate(**clean_patch)
    except ValidationError as exc:
        logger.warning("Interaction patch failed validation", extra={"session_id": context.session_id, "errors": exc.errors()})
        return context.validation_error("Unable to validate requested interaction edits.", exc)

    logger.info(
        "Updating interaction fields",
        extra={"session_id": context.session_id, "interaction_id": interaction_id, "updated_fields": sorted(clean_patch.keys())},
    )
    interaction = context.repository.update_interaction(interaction_id, update)
    return {
        "interaction": InteractionRead.model_validate(interaction).model_dump(mode="json"),
        "updated_fields": sorted(clean_patch.keys()),
    }
