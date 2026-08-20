import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class CreditFactor(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Credit/Discredit.CreditFactor — a definable reason credit points are awarded."""

    __tablename__ = "credit_factors"

    code: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    default_weight: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)


class DiscreditFactor(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Credit/Discredit.DiscreditFactor — a definable reason discredit points are applied."""

    __tablename__ = "discredit_factors"

    code: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    default_weight: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)


class CreditLedger(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Credit/Discredit.CreditLedger — an immutable, traceable entry.

    Critical Rule: every score must be traceable back to the Factor and
    Evidence/Report that produced it — never store only the final score.

    Score formula: Credit Score = Σ(Credit Factor Weight * Factor Status Factor).
    `factor_weight` and `status_factor` are captured at write-time (so later
    edits to a CreditFactor's default weight never retroactively rewrite
    history) and `points` is their product, stored for fast aggregation.
    """

    __tablename__ = "credit_ledger"

    seller_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("sellers.id", ondelete="CASCADE"), nullable=False
    )
    credit_factor_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("credit_factors.id"), nullable=False
    )
    report_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("reports.id", ondelete="SET NULL"), nullable=True
    )
    evidence_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("evidences.id", ondelete="SET NULL"), nullable=True
    )
    factor_weight: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    status_factor: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    points: Mapped[float] = mapped_column(Float, nullable=False)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)


class DiscreditLedger(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Credit/Discredit.DiscreditLedger — an immutable, traceable entry.

    Score formula: Discredit Score = Σ(Discredit Factor Weight * Verification
    Impact Multiplier). An entry is only ever created when a Report becomes
    VERIFIED. Dispute-First Architecture: if the Seller later wins an appeal
    the entry is never deleted (Traceability Rule) — it is flagged
    `is_voided` and excluded from score recalculation instead.
    """

    __tablename__ = "discredit_ledger"

    seller_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("sellers.id", ondelete="CASCADE"), nullable=False
    )
    discredit_factor_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("discredit_factors.id"), nullable=False
    )
    report_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("reports.id", ondelete="SET NULL"), nullable=True
    )
    evidence_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("evidences.id", ondelete="SET NULL"), nullable=True
    )
    factor_weight: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    verification_impact_multiplier: Mapped[float] = mapped_column(
        Float, default=1.0, nullable=False
    )
    points: Mapped[float] = mapped_column(Float, nullable=False)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Overturned-appeal void trail (Traceability Rule: never delete rows).
    is_voided: Mapped[bool] = mapped_column(default=False, nullable=False)
    voided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    voided_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    voided_reason: Mapped[str | None] = mapped_column(Text, nullable=True)


class CreditScore(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Credit/Discredit.CreditScore — current aggregated score snapshot per Seller.

    Recalculated from CreditLedger; never edited directly (Phase 4 concern).
    """

    __tablename__ = "credit_scores"
    __table_args__ = (UniqueConstraint("seller_id", name="uq_credit_scores_seller"),)

    seller_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("sellers.id", ondelete="CASCADE"), nullable=False
    )
    score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)


class DiscreditScore(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Credit/Discredit.DiscreditScore — current aggregated score snapshot per Seller."""

    __tablename__ = "discredit_scores"
    __table_args__ = (UniqueConstraint("seller_id", name="uq_discredit_scores_seller"),)

    seller_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("sellers.id", ondelete="CASCADE"), nullable=False
    )
    score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
