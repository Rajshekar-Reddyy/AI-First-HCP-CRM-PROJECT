from pydantic import BaseModel

from app.schemas.common import ToolLogRead
from app.schemas.interaction import InteractionRead
from app.schemas.reminder import ReminderRead


class DashboardRead(BaseModel):
    today_interactions: int
    pending_follow_ups: int
    positive_sentiment: int
    negative_sentiment: int
    recent_interactions: list[InteractionRead]
    pending_reminders: list[ReminderRead]
    tool_history: list[ToolLogRead]
