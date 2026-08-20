import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class CreditLedgerRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    seller_id: uuid.UUID
    credit_factor_id: uuid.UUID
    report_id: uuid.UUID | None
    evidence_id: uuid.UUID | None
    factor_weight: float
    status_factor: float
    points: float
    note: str | None
    created_at: datetime


class CreditScoreRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    seller_id: uuid.UUID
    score: float
    updated_at: datetime
