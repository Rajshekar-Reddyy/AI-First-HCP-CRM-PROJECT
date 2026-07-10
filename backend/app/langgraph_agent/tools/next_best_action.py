from typing import Any

from app.langgraph_agent.prompts import RECOMMENDATION_GENERATION_PROMPT
from app.langgraph_agent.schemas import RecommendationResponse
from app.langgraph_agent.tools.context import ToolContext
from app.schemas.interaction import InteractionRead


async def suggest_next_best_action(context: ToolContext, arguments: dict[str, Any], user_message: str) -> dict[str, Any]:
    """Analyze CRM context and return a next-best-action recommendation."""

    interaction_id = arguments.get("interaction_id") or context.latest_interaction_id()
    crm_context: dict[str, Any] = {"request": user_message}
    if interaction_id:
        crm_context["interaction"] = InteractionRead.model_validate(context.repository.get_interaction(int(interaction_id))).model_dump(mode="json")
    recommendation = await context.ai.complete_model(
        [
            {"role": "system", "content": RECOMMENDATION_GENERATION_PROMPT},
            {"role": "user", "content": str(crm_context)},
        ],
        RecommendationResponse,
    )
    return {"recommendation": recommendation.recommendation, "interaction_id": interaction_id}
