"""Governance.AuditLog writer.

Critical Rule (Traceability): every state-changing decision made by the
service layer (report review, dispute resolution, ledger voids) must be
recorded here so the platform stays 100% auditable.
"""
import uuid

from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog


def log_action(
    db: Session,
    actor_user_id: uuid.UUID | None,
    action: str,
    target_type: str,
    target_id: uuid.UUID | None,
    before: dict | None = None,
    after: dict | None = None,
) -> AuditLog:
    entry = AuditLog(
        actor_user_id=actor_user_id,
        action=action,
        target_type=target_type,
        target_id=target_id,
        before=before,
        after=after,
    )
    db.add(entry)
    return entry
