# Architecture

## Request Flow

1. The user sends a natural language instruction from the chat panel.
2. The frontend posts to `POST /chat` with `stream: true`.
3. FastAPI creates a `CRMGraph` for the request session.
4. The LangGraph `decide_tool` node sends the tool-selection prompt, conversation memory, and active interaction context to Groq.
5. Groq returns JSON selecting one of the seven tools with arguments, and the response is validated with Pydantic before routing.
6. Conditional edges route to the selected tool node. The tool writes or reads MySQL through the repository layer and records a `tool_logs` row.
7. The `respond` node asks Groq to summarize the result in markdown.
8. FastAPI streams status, tool, token, and done events to the UI.
9. Redux updates chat messages, current tool, dashboard data, and the read-only interaction form.

## Backend Layers

- Routes validate HTTP payloads and translate domain errors.
- Services coordinate use cases.
- Repositories isolate SQLAlchemy queries and persistence.
- Schemas define API contracts with Pydantic.
- LangGraph modules isolate prompts, state, Groq transport, graph nodes, and tool implementations.
- Each CRM tool lives in its own module under `backend/app/langgraph_agent/tools/`; `tools/__init__.py` exposes the registry-backed executor used by graph nodes.

## Frontend State

- `chat`: session id, message history, streaming status, current tool, model, local tool log, toast.
- `interaction`: active form state controlled by assistant responses.
- `dashboard`: metrics, recent activity, reminders, persisted tool logs.

## Reliability Choices

- Groq calls use retries for transient HTTP and timeout failures.
- Database connections use `pool_pre_ping` and recycling.
- Interaction edits use `exclude_unset` semantics so untouched fields are preserved.
- Tool executions are logged with full input and output JSON for auditability.
- API responses use explicit schemas for stable frontend contracts.
- AI JSON responses are parsed and validated with Pydantic before database writes.
- Malformed AI responses and provider failures return explicit API or SSE errors.
