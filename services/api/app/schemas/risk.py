import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.risk import RiskLevel


class RiskScoreRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    seller_id: uuid.UUID
    risk_level: RiskLevel
    score: float
    factors: dict | None
    calculated_at: datetime
