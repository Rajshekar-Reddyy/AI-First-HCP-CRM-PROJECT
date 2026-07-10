import json
import logging
from typing import Any

from langgraph.graph import END, StateGraph
from sqlalchemy.orm import Session

from app.langgraph_agent.groq_client import GroqClient
from app.langgraph_agent.prompts import ASSISTANT_RESPONSE_PROMPT, TOOL_SELECTION_PROMPT
from app.langgraph_agent.schemas import AssistantMarkdownResponse, ToolSelection
from app.langgraph_agent.state import AgentState
from app.langgraph_agent.tools import CRMTools, TOOL_REGISTRY
from app.repositories.crm_repository import CRMRepository
from app.schemas.interaction import InteractionRead


logger = logging.getLogger(__name__)


class CRMGraph:
    """LangGraph orchestration for AI-selected CRM tools."""

    def __init__(self, db: Session):
        self.db = db
        self.repository = CRMRepository(db)
        self.ai = GroqClient()

    def _build_messages(self, state: AgentState) -> list[dict[str, str]]:
        active = None
        if state.get("interaction_id"):
            try:
                active = InteractionRead.model_validate(self.repository.get_interaction(int(state["interaction_id"]))).model_dump(mode="json")
            except ValueError:
                active = None
        context = {
            "active_interaction": active,
            "conversation_history": state.get("messages", state.get("history", []))[-12:],
        }
        return [
            {"role": "system", "content": TOOL_SELECTION_PROMPT},
            {"role": "system", "content": f"CRM context JSON: {json.dumps(context, default=str)}"},
            {"role": "user", "content": state["user_message"]},
        ]

    async def decide_tool(self, state: AgentState) -> AgentState:
        logger.info("Received user prompt", extra={"session_id": state["session_id"], "prompt": state["user_message"]})
        decision = await self.ai.complete_model(self._build_messages(state), ToolSelection)
        state["selected_tool"] = decision.tool
        state["tool_arguments"] = decision.arguments
        state["tool_history"] = state.get("tool_history", []) + [{"tool": decision.tool, "reason": decision.reason}]
        logger.info(
            "LLM selected LangGraph tool",
            extra={"session_id": state["session_id"], "tool": decision.tool, "arguments": decision.arguments},
        )
        return state

    async def execute_tool(self, state: AgentState) -> AgentState:
        tool_name = state.get("selected_tool")
        tools = CRMTools(self.db, self.ai, state["session_id"])
        result = await tools.run(str(tool_name), state.get("tool_arguments") or {}, state["user_message"])
        status = "error" if "error" in result else "success"
        self.repository.log_tool(state["session_id"], str(tool_name), state.get("tool_arguments") or {}, result, status)
        state["tool_result"] = result
        if result.get("interaction"):
            state["current_interaction"] = result["interaction"]
            state["interaction_id"] = result["interaction"]["id"]
            logger.info(
                "Interaction state updated by tool",
                extra={"session_id": state["session_id"], "tool": tool_name, "interaction_id": state["interaction_id"]},
            )
        if result.get("reminder"):
            state["reminders"] = state.get("reminders", []) + [result["reminder"]]
            logger.info("Reminder state updated by tool", extra={"session_id": state["session_id"], "tool": tool_name})
        if result.get("error"):
            logger.warning("Tool returned domain error", extra={"session_id": state["session_id"], "tool": tool_name, "result": result})
        return state

    async def tool_selection_error(self, state: AgentState) -> AgentState:
        state["tool_result"] = {"error": f"Unsupported tool selected: {state.get('selected_tool')}"}
        logger.warning("Unsupported tool selection reached graph error node", extra={"session_id": state.get("session_id"), "tool": state.get("selected_tool")})
        return state

    async def respond(self, state: AgentState) -> AgentState:
        content = await self.ai.complete(self.response_messages(state))
        AssistantMarkdownResponse(message=content)
        state["response"] = content
        self.save_response(state, content)
        return state

    def response_messages(self, state: AgentState) -> list[dict[str, str]]:
        return [
            {"role": "system", "content": ASSISTANT_RESPONSE_PROMPT},
            {"role": "user", "content": json.dumps({"request": state["user_message"], "tool": state.get("selected_tool"), "result": state.get("tool_result")}, default=str)},
        ]

    def save_response(self, state: AgentState, content: str) -> None:
        self.repository.add_chat_message(state["session_id"], "user", state["user_message"])
        self.repository.add_chat_message(state["session_id"], "assistant", content)

    def compile(self):
        graph = StateGraph(AgentState)
        graph.add_node("decide_tool", self.decide_tool)
        for tool_name in TOOL_REGISTRY:
            graph.add_node(tool_name, self.execute_tool)
        graph.add_node("tool_selection_error", self.tool_selection_error)
        graph.add_node("respond", self.respond)
        graph.set_entry_point("decide_tool")
        graph.add_conditional_edges(
            "decide_tool",
            self.route_tool,
            {**{tool_name: tool_name for tool_name in TOOL_REGISTRY}, "tool_selection_error": "tool_selection_error"},
        )
        for tool_name in TOOL_REGISTRY:
            graph.add_edge(tool_name, "respond")
        graph.add_edge("tool_selection_error", "respond")
        graph.add_edge("respond", END)
        return graph.compile()

    def route_tool(self, state: AgentState) -> str:
        selected_tool = state.get("selected_tool")
        if selected_tool not in TOOL_REGISTRY:
            logger.warning("Routing rejected unsupported tool", extra={"session_id": state.get("session_id"), "tool": selected_tool})
            return "tool_selection_error"
        return str(selected_tool)

    async def invoke(self, session_id: str, message: str, interaction_id: int | None = None) -> AgentState:
        app = self.compile()
        return await app.ainvoke(self.initial_state(session_id, message, interaction_id))

    def initial_state(self, session_id: str, message: str, interaction_id: int | None = None) -> AgentState:
        history = [{"role": row.role, "content": row.content} for row in self.repository.chat_history(session_id)]
        return {
            "session_id": session_id,
            "user_message": message,
            "interaction_id": interaction_id,
            "history": history,
            "messages": [*history, {"role": "user", "content": message}],
            "tool_history": [],
            "reminders": [],
            "hcp_context": {},
        }
