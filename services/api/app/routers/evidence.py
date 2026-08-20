import uuid

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.permissions import Role, require_roles
from app.core.storage import resolve_evidence_path
from app.database.session import get_db
from app.models.evidence import Evidence
from app.models.report import Report
from app.models.user import User
from app.schemas.evidence import EvidenceCreate, EvidenceRead
from app.services import evidence_service

router = APIRouter(prefix="/evidence", tags=["evidence"])

# Phase 3 will replace this with real object storage + full validation.
ALLOWED_FILE_SIZE_BYTES = 25 * 1024 * 1024  # 25 MB foundation limit


@router.post("", response_model=EvidenceRead, status_code=status.HTTP_201_CREATED)
def create_evidence(
    data: EvidenceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(Role.USER, Role.ADMIN, Role.OFFICER)),
):
    """Register evidence that is already hosted elsewhere (external URL)."""
    if data.file_size_bytes > ALLOWED_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="Evidence file exceeds the maximum allowed size.",
        )
    evidence = Evidence(**data.model_dump(), uploaded_by=current_user.id)
    db.add(evidence)
    db.commit()
    db.refresh(evidence)
    return evidence


@router.post("/upload", response_model=EvidenceRead, status_code=status.HTTP_201_CREATED)
def upload_evidence(
    report_id: uuid.UUID = Form(...),
    comment: str | None = Form(None),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(Role.USER, Role.ADMIN, Role.OFFICER)),
):
    """Real file upload — Phase 3 local disk storage backend.

    Streams the file to disk, computes a SHA-256 hash for "สลิปเดียวกัน"
    duplicate detection, and validates the file type against a whitelist.
    """
    report = db.get(Report, report_id)
    if report is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found")

    return evidence_service.upload_evidence(
        db, report_id=report_id, upload=file, uploaded_by=current_user.id, comment=comment
    )


@router.get("/report/{report_id}", response_model=list[EvidenceRead])
def list_evidence_for_report(report_id: uuid.UUID, db: Session = Depends(get_db)):
    """'ดูรายละเอียดหลักฐานได้' is granted to both Public and User."""
    stmt = select(Evidence).where(Evidence.report_id == report_id)
    return list(db.execute(stmt).scalars())


@router.get("/{evidence_id}/file")
def download_evidence_file(evidence_id: uuid.UUID, db: Session = Depends(get_db)):
    """Stream back an uploaded evidence file from local disk storage."""
    evidence = db.get(Evidence, evidence_id)
    if evidence is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evidence not found")
    path = resolve_evidence_path(evidence.file_url)
    return FileResponse(path)
