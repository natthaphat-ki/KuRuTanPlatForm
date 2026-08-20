import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class DisputeStatus(str, enum.Enum):
    """Dispute & Appeal Lifecycle status.

    PENDING  -> Seller submitted a dispute with counter evidence; queued for
                Officer/Admin review. The related Report moves to APPEALED.
    APPROVED -> Overturned: the related DiscreditLedger entry is voided and
                the Score is recalculated back in the Seller's favor.
    REJECTED -> Appeal rejected: the Discredit Score is maintained as-is.
    """

    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class Dispute(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Governance.Dispute — a Seller's Appeal against a Report/Verification.

    Critical Rule: Dispute/Appeal must exist in the architecture from the
    start, not bolted on later.
    """

    __tablename__ = "disputes"

    report_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("reports.id", ondelete="CASCADE"), nullable=False
    )
    seller_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("sellers.id", ondelete="CASCADE"), nullable=False
    )
    submitted_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    counter_evidence: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    status: Mapped[DisputeStatus] = mapped_column(
        Enum(DisputeStatus, name="dispute_status"), default=DisputeStatus.PENDING, nullable=False
    )
    resolved_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    resolution_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
