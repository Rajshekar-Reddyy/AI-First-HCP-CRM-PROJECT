from typing import Any, TypedDict


class AgentState(TypedDict, total=False):
    session_id: str
    user_message: str
    interaction_id: int | None
    history: list[dict[str, str]]
    messages: list[dict[str, str]]
    current_interaction: dict[str, Any] | None
    hcp_context: dict[str, Any]
    reminders: list[dict[str, Any]]
    tool_history: list[dict[str, Any]]
    selected_tool: str | None
    tool_arguments: dict[str, Any]
    tool_result: dict[str, Any]
    response: str
