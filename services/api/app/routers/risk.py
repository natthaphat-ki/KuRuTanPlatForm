"""Risk router — Phase 2 read-only foundation; Fraud Risk Engine is Phase 5."""
import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.schemas.risk import RiskScoreRead
from app.services import risk_service

router = APIRouter(prefix="/risk", tags=["risk"])


@router.get("/{seller_id}", response_model=list[RiskScoreRead])
def get_risk_scores(seller_id: uuid.UUID, db: Session = Depends(get_db)):
    return risk_service.list_risk_scores_for_seller(db, seller_id)
