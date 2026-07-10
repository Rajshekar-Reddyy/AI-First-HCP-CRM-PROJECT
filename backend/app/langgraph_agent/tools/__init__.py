import logging
from collections.abc import Awaitable, Callable
from typing import Any

from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.langgraph_agent.groq_client import GroqClient
from app.langgraph_agent.tools.context import ToolContext, ToolExecutionError
from app.langgraph_agent.tools.edit_interaction import edit_interaction
from app.langgraph_agent.tools.log_interaction import log_interaction
from app.langgraph_agent.tools.meeting_summary import generate_meeting_summary
from app.langgraph_agent.tools.next_best_action import suggest_next_best_action
from app.langgraph_agent.tools.product_information import product_information
from app.langgraph_agent.tools.schedule_reminder import schedule_reminder
from app.langgraph_agent.tools.search_history import search_hcp_history


logger = logging.getLogger(__name__)
ToolCallable = Callable[[ToolContext, dict[str, Any], str], Awaitable[dict[str, Any]]]


TOOL_REGISTRY: dict[str, ToolCallable] = {
    "log_interaction": log_interaction,
    "edit_interaction": edit_interaction,
    "search_hcp_history": search_hcp_history,
    "generate_meeting_summary": generate_meeting_summary,
    "suggest_next_best_action": suggest_next_best_action,
    "product_information": product_information,
    "schedule_reminder": schedule_reminder,
}


class CRMTools:
    """Registry-backed LangGraph tool executor."""

    def __init__(self, db: Session, ai: GroqClient, session_id: str):
        self.context = ToolContext(db, ai, session_id)

    async def run(self, tool_name: str, arguments: dict[str, Any], user_message: str) -> dict[str, Any]:
        tool = TOOL_REGISTRY.get(tool_name)
        if tool is None:
            logger.warning("Unsupported LangGraph tool selected", extra={"session_id": self.context.session_id, "tool": tool_name})
            return {"error": f"Unsupported tool: {tool_name}"}
        try:
            return await tool(self.context, arguments, user_message)
        except ToolExecutionError as exc:
            logger.info("Tool execution rejected request", extra={"session_id": self.context.session_id, "tool": tool_name, "error": str(exc)})
            return {"error": str(exc)}
        except ValidationError as exc:
            logger.warning("Tool argument validation failed", extra={"session_id": self.context.session_id, "tool": tool_name, "errors": exc.errors()})
            return {"error": "The assistant produced invalid tool arguments.", "details": exc.errors()}
