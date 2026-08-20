import uuid

from pydantic import BaseModel, ConfigDict


class FraudPatternRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    code: str
    name: str
    description: str | None
    pattern_definition: dict | None
