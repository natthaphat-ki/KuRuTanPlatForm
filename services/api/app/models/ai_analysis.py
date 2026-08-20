import uuid

from sqlalchemy import String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class AIAnalysis(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Fraud Intelligence.AIAnalysis — generic result container for AI Service output.

    `target_type`/`target_id` point at any domain entity (Seller, Report, ...),
    keeping this table generic so Phase 6 AI features can plug in without
    schema churn.
    """

    __tablename__ = "ai_analyses"

    target_type: Mapped[str] = mapped_column(String(100), nullable=False)
    target_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    analysis_type: Mapped[str] = mapped_column(String(100), nullable=False)
    result: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    model_used: Mapped[str | None] = mapped_column(String(255), nullable=True)
