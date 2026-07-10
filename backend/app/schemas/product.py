from pydantic import BaseModel

from app.schemas.common import ORMModel


class ProductRead(ORMModel):
    id: int
    name: str
    benefits: str
    dosage: str
    side_effects: str
    clinical_notes: str


class ProductSearch(BaseModel):
    query: str | None = None
