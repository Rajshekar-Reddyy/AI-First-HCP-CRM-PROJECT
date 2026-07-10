from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.repositories.crm_repository import CRMRepository
from app.schemas.interaction import InteractionRead

router = APIRouter(prefix="/hcp", tags=["hcp"])


@router.get("/history", response_model=list[InteractionRead])
def hcp_history(name: str = Query(min_length=1), db: Session = Depends(get_db)):
    return CRMRepository(db).search_hcp_history(name)
