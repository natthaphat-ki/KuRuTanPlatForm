"""Report Lifecycle service.

[User Submit] -> UNVERIFIED -> [Duplicate Check]
                                      |
                                      v
[Discredit Score Updated] <- VERIFIED <- [Officer Review] -> REJECTED
"""
import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.credit import DiscreditFactor
from app.models.evidence import Evidence, EvidenceFileType, Verification, VerificationStatus
from app.models.report import Report, ReportStatus
from app.schemas.report import ReportCreate
from app.services import audit_service, discredit_service


def _find_duplicate(db: Session, seller_id: uuid.UUID, reference_key: str | None) -> Report | None:
    """Basic Duplicate Check: same seller + same reference key (e.g. bank
    account no., PromptPay no., slip/tracking no.) on a report that hasn't
    already been rejected/voided.
    """
    if not reference_key:
        return None
    stmt = select(Report).where(
        Report.seller_id == seller_id,
        Report.reference_key == reference_key,
        Report.status.notin_([ReportStatus.REJECTED, ReportStatus.VOIDED]),
    )
    return db.execute(stmt).scalars().first()


def create_report(db: Session, data: ReportCreate, reporter_user_id: uuid.UUID | None) -> Report:
    duplicate = _find_duplicate(db, data.seller_id, data.reference_key)

    report = Report(
        **data.model_dump(),
        reporter_user_id=reporter_user_id,
        duplicate_of_report_id=duplicate.id if duplicate else None,
    )
    db.add(report)
    db.flush()

    if duplicate is not None:
        audit_service.log_action(
            db,
            actor_user_id=reporter_user_id,
            action="report.flagged_duplicate",
            target_type="report",
            target_id=report.id,
            after={"duplicate_of_report_id": str(duplicate.id)},
        )
    audit_service.log_action(
        db,
        actor_user_id=reporter_user_id,
        action="report.created",
        target_type="report",
        target_id=report.id,
        after={"status": report.status.value, "seller_id": str(report.seller_id)},
    )

    db.commit()
    db.refresh(report)
    return report


def list_reports(
    db: Session, seller_id: uuid.UUID | None = None, skip: int = 0, limit: int = 50
) -> list[Report]:
    stmt = select(Report)
    if seller_id is not None:
        stmt = stmt.where(Report.seller_id == seller_id)
    stmt = stmt.offset(skip).limit(limit)
    return list(db.execute(stmt).scalars())


def list_my_reports(
    db: Session, reporter_user_id: uuid.UUID, skip: int = 0, limit: int = 50
) -> list[Report]:
    stmt = (
        select(Report)
        .where(Report.reporter_user_id == reporter_user_id)
        .offset(skip)
        .limit(limit)
    )
    return list(db.execute(stmt).scalars())


def get_report(db: Session, report_id: uuid.UUID) -> Report | None:
    return db.get(Report, report_id)


def has_required_image_evidence(db: Session, report_id: uuid.UUID) -> bool:
    """Minimum Evidence Rule: at least one image is mandatory before review."""
    stmt = select(Evidence).where(
        Evidence.report_id == report_id, Evidence.file_type == EvidenceFileType.IMAGE
    )
    return db.execute(stmt).scalars().first() is not None


def submit_for_review(db: Session, report_id: uuid.UUID, actor_user_id: uuid.UUID) -> Report:
    report = get_report(db, report_id)
    if report is None:
        raise ValueError("Report not found")
    if report.status != ReportStatus.UNVERIFIED:
        raise ValueError("Only an UNVERIFIED report can be submitted for review")
    if not has_required_image_evidence(db, report_id):
        raise ValueError("At least one image evidence is required before review")

    before_status = report.status.value
    report.status = ReportStatus.PENDING_REVIEW
    audit_service.log_action(
        db,
        actor_user_id=actor_user_id,
        action="report.submitted_for_review",
        target_type="report",
        target_id=report.id,
        before={"status": before_status},
        after={"status": report.status.value},
    )
    db.commit()
    db.refresh(report)
    return report


def review_report(
    db: Session,
    report_id: uuid.UUID,
    decision: str,
    actor_user_id: uuid.UUID,
    discredit_factor_id: uuid.UUID | None = None,
    note: str | None = None,
) -> Report:
    """Officer Review decision.

    decision="verified" -> Report VERIFIED, DiscreditLedger entry created,
                            Discredit Score recalculated (Presumption of
                            Innocence Rule no longer applies once verified).
    decision="rejected"  -> Report REJECTED, no Score impact, process ends.
    """
    report = get_report(db, report_id)
    if report is None:
        raise ValueError("Report not found")
    if report.status not in (ReportStatus.UNVERIFIED, ReportStatus.PENDING_REVIEW):
        raise ValueError("Report is not awaiting review")
    if decision not in ("verified", "rejected"):
        raise ValueError("decision must be 'verified' or 'rejected'")
    if decision == "verified" and discredit_factor_id is None:
        raise ValueError("discredit_factor_id is required to verify a report")

    before_status = report.status.value

    if decision == "verified":
        report.status = ReportStatus.VERIFIED
        verification = Verification(
            report_id=report.id,
            verified_by=actor_user_id,
            status=VerificationStatus.VERIFIED,
            notes=note,
        )
        db.add(verification)

        factor = db.get(DiscreditFactor, discredit_factor_id)
        if factor is None:
            raise ValueError("DiscreditFactor not found")

        db.flush()
        discredit_service.apply_discredit(
            db,
            seller_id=report.seller_id,
            discredit_factor_id=factor.id,
            factor_weight=factor.default_weight,
            verification_impact_multiplier=1.0,
            report_id=report.id,
            note=note,
        )
    else:
        report.status = ReportStatus.REJECTED
        verification = Verification(
            report_id=report.id,
            verified_by=actor_user_id,
            status=VerificationStatus.REJECTED,
            notes=note,
        )
        db.add(verification)

    audit_service.log_action(
        db,
        actor_user_id=actor_user_id,
        action=f"report.{decision}",
        target_type="report",
        target_id=report.id,
        before={"status": before_status},
        after={"status": report.status.value},
    )

    db.commit()
    db.refresh(report)
    return report
