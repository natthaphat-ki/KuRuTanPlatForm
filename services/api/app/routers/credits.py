import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.schemas.credit import CreditLedgerRead, CreditScoreRead
from app.services import credit_service

router = APIRouter(prefix="/credits", tags=["credits"])


@router.get("/{seller_id}/ledger", response_model=list[CreditLedgerRead])
def get_credit_ledger(seller_id: uuid.UUID, db: Session = Depends(get_db)):
    return credit_service.list_ledger_for_seller(db, seller_id)


@router.get("/{seller_id}/score", response_model=CreditScoreRead | None)
def get_credit_score(seller_id: uuid.UUID, db: Session = Depends(get_db)):
    return credit_service.get_score_for_seller(db, seller_id)
