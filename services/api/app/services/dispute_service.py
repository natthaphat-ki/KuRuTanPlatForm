"""Dispute & Appeal Lifecycle service.

[Seller Dispute] -> APPEALED -> [Officer Review]
                                       |
                    Approved: VOIDED (void ledger + recalc score)
                    Rejected: back to VERIFIED (score maintained)
"""
import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.dispute import Dispute, DisputeStatus
from app.models.report import Report, ReportStatus
from app.schemas.dispute import DisputeCreate
from app.services import audit_service, discredit_service


def create_dispute(db: Session, data: DisputeCreate, submitted_by: uuid.UUID | None) -> Dispute:
    report = db.get(Report, data.report_id)
    if report is None:
        raise ValueError("Report not found")
    if report.status != ReportStatus.VERIFIED:
        raise ValueError("Only a VERIFIED report can be disputed")

    dispute = Dispute(**data.model_dump(), submitted_by=submitted_by)
    db.add(dispute)

    before_status = report.status.value
    report.status = ReportStatus.APPEALED

    db.flush()
    audit_service.log_action(
        db,
        actor_user_id=submitted_by,
        action="dispute.created",
        target_type="report",
        target_id=report.id,
        before={"status": before_status},
        after={"status": report.status.value, "dispute_id": str(dispute.id)},
    )

    db.commit()
    db.refresh(dispute)
    return dispute


def list_disputes(
    db: Session, seller_id: uuid.UUID | None = None, skip: int = 0, limit: int = 50
) -> list[Dispute]:
    stmt = select(Dispute)
    if seller_id is not None:
        stmt = stmt.where(Dispute.seller_id == seller_id)
    stmt = stmt.offset(skip).limit(limit)
    return list(db.execute(stmt).scalars())


def get_dispute(db: Session, dispute_id: uuid.UUID) -> Dispute | None:
    return db.get(Dispute, dispute_id)


def resolve_dispute(
    db: Session,
    dispute_id: uuid.UUID,
    decision: str,
    actor_user_id: uuid.UUID,
    resolution_notes: str | None = None,
) -> Dispute:
    if decision not in ("approved", "rejected"):
        raise ValueError("decision must be 'approved' or 'rejected'")

    dispute = get_dispute(db, dispute_id)
    if dispute is None:
        raise ValueError("Dispute not found")
    if dispute.status != DisputeStatus.PENDING:
        raise ValueError("Dispute has already been resolved")

    report = db.get(Report, dispute.report_id)
    if report is None:
        raise ValueError("Report not found")

    dispute.resolved_by = actor_user_id
    dispute.resolution_notes = resolution_notes
    dispute.resolved_at = datetime.now(timezone.utc)

    before_status = report.status.value

    if decision == "approved":
        # Appeal Approved -> Overturn: void the ledger entry, recalculate score.
        dispute.status = DisputeStatus.APPROVED
        report.status = ReportStatus.VOIDED
        discredit_service.void_ledger_entries_for_report(
            db,
            report_id=report.id,
            voided_by=actor_user_id,
            voided_reason=resolution_notes or "Appeal approved: report overturned.",
        )
    else:
        # Appeal Rejected -> maintain the Discredit Score, report stays VERIFIED.
        dispute.status = DisputeStatus.REJECTED
        report.status = ReportStatus.VERIFIED

    audit_service.log_action(
        db,
        actor_user_id=actor_user_id,
        action=f"dispute.{decision}",
        target_type="dispute",
        target_id=dispute.id,
        before={"report_status": before_status},
        after={"report_status": report.status.value, "dispute_status": dispute.status.value},
    )

    db.commit()
    db.refresh(dispute)
    return dispute
