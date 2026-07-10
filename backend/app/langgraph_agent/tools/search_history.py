from typing import Any

from app.langgraph_agent.schemas import HCPHistoryArguments
from app.langgraph_agent.tools.context import ToolContext
from app.schemas.interaction import InteractionRead


async def search_hcp_history(context: ToolContext, arguments: dict[str, Any], user_message: str) -> dict[str, Any]:
    """Retrieve previous meetings and follow-up context for an HCP."""

    raw = {"hcp_name": arguments.get("hcp_name") or arguments.get("name") or user_message, "limit": arguments.get("limit", 8)}
    parsed = HCPHistoryArguments(**raw)
    rows = context.repository.search_hcp_history(parsed.hcp_name, parsed.limit)
    return {"history": [InteractionRead.model_validate(row).model_dump(mode="json") for row in rows]}
