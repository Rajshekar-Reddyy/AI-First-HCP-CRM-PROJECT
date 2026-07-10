from datetime import datetime

from pydantic import BaseModel

from app.schemas.common import ORMModel


class ReminderCreate(BaseModel):
    hcp_id: int
    interaction_id: int | None = None
    title: str
    due_at: datetime
    notes: str | None = None


class ReminderRead(ORMModel):
    id: int
    hcp_id: int
    interaction_id: int | None = None
    title: str
    due_at: datetime
    status: str
    notes: str | None = None
