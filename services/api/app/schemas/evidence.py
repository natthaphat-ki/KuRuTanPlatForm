import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.evidence import EvidenceFileType


class EvidenceCreate(BaseModel):
    """External-URL evidence (already hosted elsewhere, e.g. a marketplace
    screenshot link). For real file uploads use `POST /evidence/upload`.
    """

    report_id: uuid.UUID
    file_url: str
    file_type: EvidenceFileType
    file_size_bytes: int
    file_metadata: dict | None = None
    comment: str | None = None


class EvidenceRead(EvidenceCreate):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    uploaded_by: uuid.UUID | None
    file_hash: str | None = None
    duplicate_of_evidence_id: uuid.UUID | None = None
    created_at: datetime
