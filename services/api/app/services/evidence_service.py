"""Evidence upload service — Phase 3.

Handles the real file-upload path: saves the file via app.core.storage,
runs the "สลิปเดียวกัน" (same file) duplicate check by SHA-256 hash across
all Evidence rows, and records the resulting Evidence (+ audit trail).
"""
import uuid

from fastapi import UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.storage import save_evidence_file
from app.models.evidence import Evidence
from app.services import audit_service


def _find_duplicate_by_hash(
    db: Session, file_hash: str, exclude_report_id: uuid.UUID
) -> Evidence | None:
    stmt = (
        select(Evidence)
        .where(Evidence.file_hash == file_hash, Evidence.report_id != exclude_report_id)
        .order_by(Evidence.created_at.asc())
    )
    return db.execute(stmt).scalars().first()


def upload_evidence(
    db: Session,
    report_id: uuid.UUID,
    upload: UploadFile,
    uploaded_by: uuid.UUID,
    comment: str | None = None,
) -> Evidence:
    stored = save_evidence_file(report_id, upload)

    duplicate = _find_duplicate_by_hash(db, stored["file_hash"], exclude_report_id=report_id)

    evidence = Evidence(
        report_id=report_id,
        uploaded_by=uploaded_by,
        file_url=stored["relative_path"],
        file_type=stored["file_type"],
        file_size_bytes=stored["file_size_bytes"],
        file_hash=stored["file_hash"],
        comment=comment,
        duplicate_of_evidence_id=duplicate.id if duplicate else None,
    )
    db.add(evidence)
    db.flush()

    if duplicate is not None:
        audit_service.log_action(
            db,
            actor_user_id=uploaded_by,
            action="evidence.flagged_duplicate",
            target_type="evidence",
            target_id=evidence.id,
            after={
                "duplicate_of_evidence_id": str(duplicate.id),
                "duplicate_of_report_id": str(duplicate.report_id),
            },
        )

    audit_service.log_action(
        db,
        actor_user_id=uploaded_by,
        action="evidence.uploaded",
        target_type="evidence",
        target_id=evidence.id,
        after={"report_id": str(report_id), "file_type": stored["file_type"].value},
    )

    db.commit()
    db.refresh(evidence)
    return evidence
