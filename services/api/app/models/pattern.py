import uuid

from sqlalchemy import String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class FraudPattern(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Fraud Intelligence.FraudPattern — Phase 5 output, foundation table only for now."""

    __tablename__ = "fraud_patterns"

    code: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    pattern_definition: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
