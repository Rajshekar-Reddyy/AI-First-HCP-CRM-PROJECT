from typing import Any

from pydantic import BaseModel, Field

from app.schemas.common import ToolLogRead
from app.schemas.interaction import InteractionRead
from app.schemas.reminder import ReminderRead


class ChatRequest(BaseModel):
    session_id: str = Field(default="default")
    message: str = Field(min_length=1)
    interaction_id: int | None = None
    stream: bool = True


class ChatResponse(BaseModel):
    message: str
    current_tool: str | None = None
    interaction: InteractionRead | None = None
    reminders: list[ReminderRead] = []
    tool_logs: list[ToolLogRead] = []
    metadata: dict[str, Any] = {}
