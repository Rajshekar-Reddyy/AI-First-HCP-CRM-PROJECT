from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class ToolLogRead(ORMModel):
    id: int
    session_id: str
    tool_name: str
    input_json: str
    output_json: str
    status: str
    created_at: datetime
