"""Fraud pattern router — Phase 2 read-only foundation; logic lands in Phase 5."""
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.pattern import FraudPattern
from app.schemas.pattern import FraudPatternRead

router = APIRouter(prefix="/patterns", tags=["patterns"])


@router.get("", response_model=list[FraudPatternRead])
def list_patterns(db: Session = Depends(get_db)):
    return list(db.execute(select(FraudPattern)).scalars())
