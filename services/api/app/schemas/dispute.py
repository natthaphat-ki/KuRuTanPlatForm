import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.dispute import DisputeStatus


class DisputeCreate(BaseModel):
    report_id: uuid.UUID
    seller_id: uuid.UUID
    reason: str
    counter_evidence: dict | None = None


class DisputeRead(DisputeCreate):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    submitted_by: uuid.UUID | None
    status: DisputeStatus
    resolved_by: uuid.UUID | None
    resolution_notes: str | None
    created_at: datetime
    resolved_at: datetime | None


class DisputeResolveDecision(BaseModel):
    """Officer/Admin resolution payload for an Appeal."""

    decision: str  # "approved" | "rejected"
    resolution_notes: str | None = None
