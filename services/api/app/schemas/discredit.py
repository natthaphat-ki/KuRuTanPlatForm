import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class DiscreditLedgerRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    seller_id: uuid.UUID
    discredit_factor_id: uuid.UUID
    report_id: uuid.UUID | None
    evidence_id: uuid.UUID | None
    factor_weight: float
    verification_impact_multiplier: float
    points: float
    note: str | None
    is_voided: bool
    voided_at: datetime | None
    voided_reason: str | None
    created_at: datetime


class DiscreditScoreRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    seller_id: uuid.UUID
    score: float
    updated_at: datetime
