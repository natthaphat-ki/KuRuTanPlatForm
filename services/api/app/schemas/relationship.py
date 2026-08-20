import uuid

from pydantic import BaseModel, ConfigDict


class RelationshipRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    seller_id_a: uuid.UUID
    seller_id_b: uuid.UUID
    relationship_type: str
    confidence: float
    evidence: dict | None
