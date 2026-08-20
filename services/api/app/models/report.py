import enum
import uuid

from sqlalchemy import Enum, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class ReportStatus(str, enum.Enum):
    """Verification Status Rules (2.3):

    UNVERIFIED     -> just submitted, shown in Public View "under review" zone,
                       never affects Score (Presumption of Innocence Rule).
    PENDING_REVIEW -> queued for an Officer/Admin to review.
    VERIFIED       -> evidence confirmed; a DiscreditLedger entry is created
                       and the Seller's Discredit Score is recalculated.
    REJECTED       -> insufficient/false evidence; no Score impact, process ends.
    APPEALED       -> the Seller has opened a Dispute against a VERIFIED report.
    VOIDED         -> the appeal was upheld; the related Ledger entry is voided
                       and the Score is recalculated back in the Seller's favor.
    """

    UNVERIFIED = "unverified"
    PENDING_REVIEW = "pending_review"
    VERIFIED = "verified"
    REJECTED = "rejected"
    APPEALED = "appealed"
    VOIDED = "voided"


class ReportVisibility(str, enum.Enum):
    PUBLIC = "public"
    PRIVATE = "private"


class Report(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Evidence.Report — a Credit/Discredit-worthy claim submitted about a Seller.

    Critical Rule: an un-verified report must never be interpreted as proven
    wrongdoing, so status defaults to PENDING and only Verification changes it.
    """

    __tablename__ = "reports"

    reporter_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    seller_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("sellers.id", ondelete="CASCADE"), nullable=False
    )
    category: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[ReportStatus] = mapped_column(
        Enum(ReportStatus, name="report_status"), default=ReportStatus.UNVERIFIED, nullable=False
    )
    visibility: Mapped[ReportVisibility] = mapped_column(
        Enum(ReportVisibility, name="report_visibility"),
        default=ReportVisibility.PUBLIC,
        nullable=False,
    )
    # Duplicate Check: a reporter-supplied identifier (bank account no.,
    # PromptPay no., slip/tracking no.) used for basic duplicate detection.
    reference_key: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    duplicate_of_report_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("reports.id", ondelete="SET NULL"), nullable=True
    )

    evidences: Mapped[list["Evidence"]] = relationship(
        back_populates="report", cascade="all, delete-orphan"
    )
