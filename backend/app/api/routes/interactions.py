from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.interaction import InteractionCreate, InteractionRead, InteractionUpdate
from app.services.interaction_service import InteractionService

router = APIRouter(prefix="/interaction", tags=["interactions"])


@router.post("", response_model=InteractionRead)
def create_interaction(payload: InteractionCreate, db: Session = Depends(get_db)):
    return InteractionService(db).create(payload)


@router.get("/{interaction_id}", response_model=InteractionRead)
def get_interaction(interaction_id: int, db: Session = Depends(get_db)):
    try:
        return InteractionService(db).get(interaction_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.put("/{interaction_id}", response_model=InteractionRead)
def update_interaction(interaction_id: int, payload: InteractionUpdate, db: Session = Depends(get_db)):
    try:
        return InteractionService(db).update(interaction_id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
