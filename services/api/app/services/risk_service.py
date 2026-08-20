"""Risk service — Phase 2 foundation (read-only); scoring logic is Phase 5."""
import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.risk import RiskScore


def list_risk_scores_for_seller(db: Session, seller_id: uuid.UUID) -> list[RiskScore]:
    stmt = select(RiskScore).where(RiskScore.seller_id == seller_id)
    return list(db.execute(stmt).scalars())
