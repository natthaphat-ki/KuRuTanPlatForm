"""Credit scoring service.

Score formula: Credit Score = Σ(Credit Factor Weight * Factor Status Factor).
"""
import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.credit import CreditLedger, CreditScore


def list_ledger_for_seller(db: Session, seller_id: uuid.UUID) -> list[CreditLedger]:
    stmt = select(CreditLedger).where(CreditLedger.seller_id == seller_id)
    return list(db.execute(stmt).scalars())


def get_score_for_seller(db: Session, seller_id: uuid.UUID) -> CreditScore | None:
    stmt = select(CreditScore).where(CreditScore.seller_id == seller_id)
    return db.execute(stmt).scalar_one_or_none()


def apply_credit(
    db: Session,
    seller_id: uuid.UUID,
    credit_factor_id: uuid.UUID,
    factor_weight: float,
    status_factor: float = 1.0,
    report_id: uuid.UUID | None = None,
    evidence_id: uuid.UUID | None = None,
    note: str | None = None,
) -> CreditLedger:
    entry = CreditLedger(
        seller_id=seller_id,
        credit_factor_id=credit_factor_id,
        report_id=report_id,
        evidence_id=evidence_id,
        factor_weight=factor_weight,
        status_factor=status_factor,
        points=factor_weight * status_factor,
        note=note,
    )
    db.add(entry)

    score = get_score_for_seller(db, seller_id)
    if score is None:
        score = CreditScore(seller_id=seller_id, score=0.0)
        db.add(score)
    score.score += entry.points

    db.commit()
    db.refresh(entry)
    return entry
