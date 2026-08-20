import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.report import ReportStatus, ReportVisibility


class ReportBase(BaseModel):
    seller_id: uuid.UUID
    category: str
    description: str
    visibility: ReportVisibility = ReportVisibility.PUBLIC
    reference_key: str | None = None


class ReportCreate(ReportBase):
    pass


class ReportRead(ReportBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    reporter_user_id: uuid.UUID | None
    status: ReportStatus
    duplicate_of_report_id: uuid.UUID | None
    created_at: datetime
    updated_at: datetime


class ReportReviewDecision(BaseModel):
    """Officer Review payload — approve (verify) or reject a report."""

    decision: str  # "verified" | "rejected"
    discredit_factor_id: uuid.UUID | None = None
    note: str | None = None
