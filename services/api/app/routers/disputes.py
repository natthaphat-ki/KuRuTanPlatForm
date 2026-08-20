import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.permissions import Role, require_roles
from app.database.session import get_db
from app.models.user import User
from app.schemas.dispute import DisputeCreate, DisputeRead, DisputeResolveDecision
from app.services import dispute_service

router = APIRouter(prefix="/disputes", tags=["disputes"])


@router.post("", response_model=DisputeRead, status_code=201)
def create_dispute(
    data: DisputeCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(Role.USER, Role.ADMIN, Role.OFFICER)),
):
    """Dispute First Architecture — only logged-in accounts (not Public) may
    appeal a VERIFIED report."""
    try:
        return dispute_service.create_dispute(db, data, submitted_by=current_user.id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get("", response_model=list[DisputeRead])
def list_disputes(
    seller_id: uuid.UUID | None = None,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
):
    return dispute_service.list_disputes(db, seller_id=seller_id, skip=skip, limit=limit)


@router.post("/{dispute_id}/resolve", response_model=DisputeRead)
def resolve_dispute(
    dispute_id: uuid.UUID,
    data: DisputeResolveDecision,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(Role.ADMIN, Role.OFFICER)),
):
    """Officer Review of an Appeal — Admin/Officer only."""
    try:
        return dispute_service.resolve_dispute(
            db,
            dispute_id,
            decision=data.decision,
            actor_user_id=current_user.id,
            resolution_notes=data.resolution_notes,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
