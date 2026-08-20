import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.permissions import Role, require_roles
from app.database.session import get_db
from app.models.user import User
from app.schemas.report import ReportCreate, ReportRead, ReportReviewDecision
from app.services import report_service

router = APIRouter(prefix="/reports", tags=["reports"])


@router.post("", response_model=ReportRead, status_code=status.HTTP_201_CREATED)
def create_report(
    data: ReportCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(Role.USER, Role.ADMIN, Role.OFFICER)),
):
    """Public cannot create reports — 'Public ... ไม่สามารถสร้าง Report'."""
    return report_service.create_report(db, data, reporter_user_id=current_user.id)


@router.get("", response_model=list[ReportRead])
def list_reports(
    seller_id: uuid.UUID | None = None,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
):
    """Reports are visible in the Public View (UNVERIFIED shown as
    'under review', never affecting Score) so listing itself is unrestricted."""
    return report_service.list_reports(db, seller_id=seller_id, skip=skip, limit=limit)


@router.get("/mine", response_model=list[ReportRead])
def list_my_reports(
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(Role.USER, Role.ADMIN, Role.OFFICER)),
):
    """'User สามารถติดตามสถานะ Report ตัวเองแจ้งได้' — Public has no account, so
    only logged-in roles can track their own submitted reports."""
    return report_service.list_my_reports(db, current_user.id, skip=skip, limit=limit)


@router.get("/{report_id}", response_model=ReportRead)
def get_report(report_id: uuid.UUID, db: Session = Depends(get_db)):
    report = report_service.get_report(db, report_id)
    if report is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found")
    return report


@router.post("/{report_id}/submit-for-review", response_model=ReportRead)
def submit_for_review(
    report_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(Role.USER, Role.ADMIN, Role.OFFICER)),
):
    try:
        return report_service.submit_for_review(db, report_id, current_user.id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.post("/{report_id}/review", response_model=ReportRead)
def review_report(
    report_id: uuid.UUID,
    data: ReportReviewDecision,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(Role.ADMIN, Role.OFFICER)),
):
    """Officer Review decision — only Admin/Officer may verify or reject."""
    try:
        return report_service.review_report(
            db,
            report_id,
            decision=data.decision,
            actor_user_id=current_user.id,
            discredit_factor_id=data.discredit_factor_id,
            note=data.note,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
