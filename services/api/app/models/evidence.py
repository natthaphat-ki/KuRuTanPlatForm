import enum
import uuid

from sqlalchemy import BigInteger, Enum, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class EvidenceFileType(str, enum.Enum):
    IMAGE = "image"
    DOCUMENT = "document"
    VIDEO = "video"
    AUDIO = "audio"
    OTHER = "other"


class Evidence(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Evidence.Evidence — a supporting file attached to a Report."""

    __tablename__ = "evidences"

    report_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("reports.id", ondelete="CASCADE"), nullable=False
    )
    uploaded_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    file_url: Mapped[str] = mapped_column(String(1000), nullable=False)
    file_type: Mapped[EvidenceFileType] = mapped_column(
        Enum(EvidenceFileType, name="evidence_file_type"), nullable=False
    )
    file_size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)
    file_metadata: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    # "อาจจะมีข้อคอมเม้นเหตุการณ์ที่เกิดขึ้น" — optional context comment from the uploader.
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    # SHA-256 of the stored file — enables "สลิปเดียวกัน" (same slip/file)
    # duplicate detection independent of the Report-level reference_key check.
    file_hash: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    duplicate_of_evidence_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("evidences.id", ondelete="SET NULL"), nullable=True
    )

    report: Mapped["Report"] = relationship(back_populates="evidences")


class VerificationStatus(str, enum.Enum):
    PENDING = "pending"
    VERIFIED = "verified"
    REJECTED = "rejected"


class Verification(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Evidence.Verification — an Admin/Officer decision on a Report."""

    __tablename__ = "verifications"

    report_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("reports.id", ondelete="CASCADE"), nullable=False
    )
    verified_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    status: Mapped[VerificationStatus] = mapped_column(
        Enum(VerificationStatus, name="verification_status"),
        default=VerificationStatus.PENDING,
        nullable=False,
    )
    notes: Mapped[str | None] = mapped_column(String(2000), nullable=True)
