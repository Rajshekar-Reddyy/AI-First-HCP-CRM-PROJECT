from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.repositories.crm_repository import CRMRepository
from app.schemas.reminder import ReminderCreate, ReminderRead

router = APIRouter(prefix="/reminders", tags=["reminders"])


@router.post("", response_model=ReminderRead)
def create_reminder(payload: ReminderCreate, db: Session = Depends(get_db)):
    return CRMRepository(db).create_reminder(payload)
