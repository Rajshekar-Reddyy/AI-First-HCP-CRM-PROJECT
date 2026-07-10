import logging
from typing import Any

from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.langgraph_agent.groq_client import GroqClient
from app.repositories.crm_repository import CRMRepository


logger = logging.getLogger(__name__)


class ToolExecutionError(Exception):
    """Raised when a tool cannot safely update CRM state."""


class ToolContext:
    """Shared dependencies and utility methods for LangGraph tools."""

    def __init__(self, db: Session, ai: GroqClient, session_id: str):
        self.repository = CRMRepository(db)
        self.ai = ai
        self.session_id = session_id
        self.repository.seed_products_if_empty()

    def latest_interaction_id(self) -> int | None:
        latest = self.repository.latest_interaction()
        return latest.id if latest else None

    def require_interaction_id(self, value: Any) -> int:
        interaction_id = value or self.latest_interaction_id()
        if not interaction_id:
            raise ToolExecutionError("No active interaction is available for this request.")
        return int(interaction_id)

    @staticmethod
    def validation_error(message: str, exc: ValidationError) -> dict[str, Any]:
        return {"error": message, "details": exc.errors()}
