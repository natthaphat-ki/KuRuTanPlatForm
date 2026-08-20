import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.schemas.discredit import DiscreditLedgerRead, DiscreditScoreRead
from app.services import discredit_service

router = APIRouter(prefix="/discredits", tags=["discredits"])


@router.get("/{seller_id}/ledger", response_model=list[DiscreditLedgerRead])
def get_discredit_ledger(seller_id: uuid.UUID, db: Session = Depends(get_db)):
    return discredit_service.list_ledger_for_seller(db, seller_id)


@router.get("/{seller_id}/score", response_model=DiscreditScoreRead | None)
def get_discredit_score(seller_id: uuid.UUID, db: Session = Depends(get_db)):
    return discredit_service.get_score_for_seller(db, seller_id)
