from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator
from pydantic import BaseModel, Field, AliasChoices


ToolName = Literal[
    "log_interaction",
    "edit_interaction",
    "search_hcp_history",
    "generate_meeting_summary",
    "suggest_next_best_action",
    "product_information",
    "schedule_reminder",
]


class ToolSelection(BaseModel):
    """Validated model output for LangGraph tool routing."""

    tool: ToolName
    arguments: dict[str, Any] = Field(default_factory=dict)
    reason: str = Field(min_length=3, max_length=500)


class ExtractedInteractionPayload(BaseModel):
    """Raw AI extraction payload before domain schema validation."""

    model_config = ConfigDict(extra="forbid")

    hcp_name: str
    hospital: str | None = None
    specialization: str | None = None
    interaction_type: str | None = None
    interaction_date: str | None = None
    interaction_time: str | None = None
    attendees: str | None = None
    topics_discussed: str | None = None
    voice_summary: str | None = None
    materials_shared: str | None = None
    samples_distributed: str | None = None
    sentiment: Literal["positive", "neutral", "negative"] = "neutral"
    outcome: str | None = None
    follow_up: str | None = None
    notes: str | None = None

    @field_validator("hcp_name")
    @classmethod
    def hcp_name_must_not_be_blank(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("hcp_name is required")
        return cleaned


class InteractionPatchPayload(BaseModel):
    """AI-proposed partial update for a CRM interaction."""

    model_config = ConfigDict(extra="forbid")

    hcp_name: str | None = None
    hospital: str | None = None
    specialization: str | None = None
    interaction_type: str | None = None
    interaction_date: str | None = None
    interaction_time: str | None = None
    attendees: str | None = None
    topics_discussed: str | None = None
    voice_summary: str | None = None
    materials_shared: str | None = None
    samples_distributed: str | None = None
    sentiment: Literal["positive", "neutral", "negative"] | None = None
    outcome: str | None = None
    follow_up: str | None = None
    notes: str | None = None
    summary: str | None = None


class HCPHistoryArguments(BaseModel):
    hcp_name: str = Field(min_length=1)
    limit: int = Field(default=8, ge=1, le=25)


class ProductInformationArguments(BaseModel):
    query: str = Field(min_length=1)
    limit: int = Field(default=8, ge=1, le=25)


class ReminderArguments(BaseModel):
    hcp_id: int | None = None
    interaction_id: int | None = None
    title: str | None = None
    due_at: str | None = None
    date: str | None = None
    when: str | None = None
    follow_up: str | None = None
    notes: str | None = None


class SummaryResponse(BaseModel):
    summary: str = Field(min_length=20)




class RecommendationResponse(BaseModel):
    recommendation: str = Field(
        validation_alias=AliasChoices(
            "recommendation",
            "next_action",
            "action",
        ),
        min_length=5,
    )


class AssistantMarkdownResponse(BaseModel):
    message: str = Field(min_length=1)
