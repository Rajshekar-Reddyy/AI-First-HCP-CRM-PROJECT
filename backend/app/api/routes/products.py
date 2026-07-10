from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.repositories.crm_repository import CRMRepository
from app.schemas.product import ProductRead

router = APIRouter(prefix="/products", tags=["products"])


@router.get("", response_model=list[ProductRead])
def products(query: str | None = Query(default=None), db: Session = Depends(get_db)):
    repository = CRMRepository(db)
    repository.seed_products_if_empty()
    return repository.search_products(query)
