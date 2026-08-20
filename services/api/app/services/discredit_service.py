"""Discredit scoring service.

Score formula: Discredit Score = Σ(Discredit Factor Weight * Verification
Impact Multiplier), summed over non-voided ledger entries only.
"""
import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.credit import DiscreditLedger, DiscreditScore


def list_ledger_for_seller(db: Session, seller_id: uuid.UUID) -> list[DiscreditLedger]:
    stmt = select(DiscreditLedger).where(DiscreditLedger.seller_id == seller_id)
    return list(db.execute(stmt).scalars())


def get_score_for_seller(db: Session, seller_id: uuid.UUID) -> DiscreditScore | None:
    stmt = select(DiscreditScore).where(DiscreditScore.seller_id == seller_id)
    return db.execute(stmt).scalar_one_or_none()


def apply_discredit(
    db: Session,
    seller_id: uuid.UUID,
    discredit_factor_id: uuid.UUID,
    factor_weight: float,
    verification_impact_multiplier: float = 1.0,
    report_id: uuid.UUID | None = None,
    evidence_id: uuid.UUID | None = None,
    note: str | None = None,
) -> DiscreditLedger:
    entry = DiscreditLedger(
        seller_id=seller_id,
        discredit_factor_id=discredit_factor_id,
        report_id=report_id,
        evidence_id=evidence_id,
        factor_weight=factor_weight,
        verification_impact_multiplier=verification_impact_multiplier,
        points=factor_weight * verification_impact_multiplier,
        note=note,
    )
    db.add(entry)

    score = get_score_for_seller(db, seller_id)
    if score is None:
        score = DiscreditScore(seller_id=seller_id, score=0.0)
        db.add(score)
    score.score += entry.points

    db.commit()
    db.refresh(entry)
    return entry


def void_ledger_entries_for_report(
    db: Session,
    report_id: uuid.UUID,
    voided_by: uuid.UUID | None,
    voided_reason: str | None,
) -> list[DiscreditLedger]:
    """Overturned appeal: void every active ledger entry tied to this report.

    Traceability Rule: rows are never deleted, only flagged `is_voided` with
    a full audit trail (who/when/why). Caller is responsible for committing.
    """
    stmt = select(DiscreditLedger).where(
        DiscreditLedger.report_id == report_id, DiscreditLedger.is_voided.is_(False)
    )
    entries = list(db.execute(stmt).scalars())
    now = datetime.now(timezone.utc)
    seller_ids: set[uuid.UUID] = set()
    for entry in entries:
        entry.is_voided = True
        entry.voided_at = now
        entry.voided_by = voided_by
        entry.voided_reason = voided_reason
        seller_ids.add(entry.seller_id)

    # autoflush is disabled on this session (see database/session.py), so the
    # void flags above must be flushed before recalculate_score's SELECT runs
    # or it will read stale (non-voided) rows.
    db.flush()

    for seller_id in seller_ids:
        recalculate_score(db, seller_id)

    return entries


def recalculate_score(db: Session, seller_id: uuid.UUID) -> DiscreditScore:
    """Recompute the Seller's Discredit Score from non-voided ledger entries.

    Recalculating from source (instead of incrementally subtracting) keeps
    the aggregate honest even if multiple entries are voided at once.
    """
    stmt = select(DiscreditLedger).where(
        DiscreditLedger.seller_id == seller_id, DiscreditLedger.is_voided.is_(False)
    )
    entries = list(db.execute(stmt).scalars())
    total = sum(entry.points for entry in entries)

    score = get_score_for_seller(db, seller_id)
    if score is None:
        score = DiscreditScore(seller_id=seller_id, score=0.0)
        db.add(score)
    score.score = total
    return score
