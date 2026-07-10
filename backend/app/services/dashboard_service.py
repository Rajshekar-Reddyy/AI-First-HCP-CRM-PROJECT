from sqlalchemy.orm import Session

from app.repositories.crm_repository import CRMRepository


class DashboardService:
    def __init__(self, db: Session):
        self.repository = CRMRepository(db)

    def read(self) -> dict:
        return {
            **self.repository.dashboard_counts(),
            "recent_interactions": self.repository.recent_interactions(),
            "pending_reminders": self.repository.pending_reminders(),
            "tool_history": self.repository.tool_history(limit=12),
        }
