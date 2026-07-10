import json
import logging

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import AIProviderError, AIResponseValidationError, CRMError
from app.db.session import get_db
from app.langgraph_agent.graph import CRMGraph
from app.langgraph_agent.schemas import AssistantMarkdownResponse
from app.schemas.chat import ChatRequest, ChatResponse

router = APIRouter(prefix="/chat", tags=["chat"])
logger = logging.getLogger(__name__)


@router.post("", response_model=ChatResponse | None)
async def chat(request: ChatRequest, db: Session = Depends(get_db)):
    async def events():
        try:
            graph = CRMGraph(db)
            yield _event("status", {"status": "thinking", "model": settings.groq_model})
            state = graph.initial_state(request.session_id, request.message, request.interaction_id)
            state = await graph.decide_tool(state)
            yield _event("tool", {"name": state.get("selected_tool"), "arguments": state.get("tool_arguments")})
            route = graph.route_tool(state)
            state = await graph.tool_selection_error(state) if route == "tool_selection_error" else await graph.execute_tool(state)
            chunks: list[str] = []
            async for token in graph.ai.stream(graph.response_messages(state)):
                chunks.append(token)
                yield _event("token", {"content": token})
            response = "".join(chunks)
            AssistantMarkdownResponse(message=response)
            graph.save_response(state, response)
            yield _event(
                "done",
                {
                    "message": response,
                    "current_tool": state.get("selected_tool"),
                    "interaction": state.get("current_interaction"),
                    "reminders": state.get("reminders", []),
                    "metadata": {"model": settings.groq_model, "tool_result": state.get("tool_result")},
                },
            )
        except AIResponseValidationError as exc:
            logger.warning("AI response validation failed during chat stream", extra={"session_id": request.session_id, "error": str(exc)})
            yield _event("error", {"message": str(exc)})
        except AIProviderError as exc:
            logger.exception("AI provider failed during chat stream", extra={"session_id": request.session_id})
            yield _event("error", {"message": str(exc)})
        except CRMError as exc:
            logger.warning("CRM error during chat stream", extra={"session_id": request.session_id, "error": str(exc)})
            yield _event("error", {"message": str(exc)})
        except Exception as exc:
            logger.exception("Unexpected chat stream failure", extra={"session_id": request.session_id})
            yield _event("error", {"message": "The assistant could not complete the request.", "detail": str(exc)})

    if request.stream:
        return StreamingResponse(events(), media_type="text/event-stream")

    try:
        state = await CRMGraph(db).invoke(request.session_id, request.message, request.interaction_id)
        return ChatResponse(
            message=state.get("response", ""),
            current_tool=state.get("selected_tool"),
            interaction=state.get("current_interaction"),
            reminders=state.get("reminders", []),
            metadata={"model": settings.groq_model, "tool_result": state.get("tool_result")},
        )
    except AIResponseValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except AIProviderError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except CRMError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


def _event(event: str, payload: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(payload, default=str)}\n\n"
