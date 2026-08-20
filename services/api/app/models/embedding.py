import uuid

from pgvector.sqlalchemy import Vector
from sqlalchemy import String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.config import settings
from app.database.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Embedding(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """AI Data.Embedding — vector representation of any domain entity's content.

    Foundation table for Phase 6 (AI / Embedding / RAG / LLM). `source_type` +
    `source_id` generically reference a Report, Evidence, Seller, etc.
    """

    __tablename__ = "embeddings"

    source_type: Mapped[str] = mapped_column(String(100), nullable=False)
    source_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    vector: Mapped[list[float]] = mapped_column(
        Vector(settings.EMBEDDING_DIMENSION), nullable=False
    )
