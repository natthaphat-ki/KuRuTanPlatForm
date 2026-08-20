"""Relationship router — Phase 2 read-only foundation; Graph API is Phase 5."""
import uuid

from fastapi import APIRouter, Depends
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.relationship import Relationship
from app.schemas.relationship import RelationshipRead

router = APIRouter(prefix="/relationships", tags=["relationships"])


@router.get("/{seller_id}", response_model=list[RelationshipRead])
def get_relationships(seller_id: uuid.UUID, db: Session = Depends(get_db)):
    stmt = select(Relationship).where(
        or_(Relationship.seller_id_a == seller_id, Relationship.seller_id_b == seller_id)
    )
    return list(db.execute(stmt).scalars())
