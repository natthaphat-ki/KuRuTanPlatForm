"""Admin router — Role-Based Authorization Foundation showcase.

Only Admin/Officer roles may list users or read the audit log. Full
Verification Center behaviour is Phase 7.
"""
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.permissions import Role, require_roles
from app.database.session import get_db
from app.models.audit_log import AuditLog
from app.models.user import User
from app.schemas.user import UserRead

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/users", response_model=list[UserRead])
def list_users(
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(Role.ADMIN)),
):
    return list(db.execute(select(User)).scalars())


@router.get("/audit-log")
def list_audit_log(
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(Role.ADMIN, Role.OFFICER)),
):
    logs = list(db.execute(select(AuditLog).order_by(AuditLog.created_at.desc())).scalars())
    return [
        {
            "id": str(log.id),
            "actor_user_id": str(log.actor_user_id) if log.actor_user_id else None,
            "action": log.action,
            "target_type": log.target_type,
            "target_id": str(log.target_id) if log.target_id else None,
            "created_at": log.created_at,
        }
        for log in logs
    ]
