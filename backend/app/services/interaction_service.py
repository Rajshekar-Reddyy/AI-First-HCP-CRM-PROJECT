from sqlalchemy.orm import Session

from app.repositories.crm_repository import CRMRepository
from app.schemas.interaction import InteractionCreate, InteractionUpdate


class InteractionService:
    def __init__(self, db: Session):
        self.repository = CRMRepository(db)

    def create(self, data: InteractionCreate):
        return self.repository.create_interaction(data)

    def update(self, interaction_id: int, data: InteractionUpdate):
        return self.repository.update_interaction(interaction_id, data)

    def get(self, interaction_id: int):
        return self.repository.get_interaction(interaction_id)
