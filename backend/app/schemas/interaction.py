from datetime import date, time

from pydantic import BaseModel, Field

from app.models import Sentiment
from app.schemas.common import ORMModel


class HCPRead(ORMModel):
    id: int
    name: str
    hospital: str | None = None
    specialization: str | None = None


class InteractionBase(BaseModel):
    hcp_name: str = Field(min_length=1, max_length=160)
    hospital: str | None = None
    specialization: str | None = None
    interaction_type: str | None = None
    interaction_date: date | None = None
    interaction_time: time | None = None
    attendees: str | None = None
    topics_discussed: str | None = None
    voice_summary: str | None = None
    materials_shared: str | None = None
    samples_distributed: str | None = None
    sentiment: Sentiment = Sentiment.neutral
    outcome: str | None = None
    follow_up: str | None = None
    notes: str | None = None


class InteractionCreate(InteractionBase):
    """Payload for creating a complete AI-extracted interaction."""


class InteractionUpdate(BaseModel):
    hcp_name: str | None = None
    hospital: str | None = None
    specialization: str | None = None
    interaction_type: str | None = None
    interaction_date: date | None = None
    interaction_time: time | None = None
    attendees: str | None = None
    topics_discussed: str | None = None
    voice_summary: str | None = None
    materials_shared: str | None = None
    samples_distributed: str | None = None
    sentiment: Sentiment | None = None
    outcome: str | None = None
    follow_up: str | None = None
    notes: str | None = None
    summary: str | None = None


class InteractionRead(ORMModel):
    id: int
    hcp_id: int
    hcp: HCPRead
    interaction_type: str | None = None
    interaction_date: date | None = None
    interaction_time: time | None = None
    attendees: str | None = None
    topics_discussed: str | None = None
    voice_summary: str | None = None
    materials_shared: str | None = None
    samples_distributed: str | None = None
    sentiment: Sentiment
    outcome: str | None = None
    follow_up: str | None = None
    notes: str | None = None
    summary: str | None = None
