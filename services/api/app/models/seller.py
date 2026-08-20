import enum
import uuid

from sqlalchemy import Enum, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class SellerEntityType(str, enum.Enum):
    INDIVIDUAL = "individual"
    BUSINESS = "business"


class Seller(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Identity.Seller — the merchant/seller entity Credit & Discredit attach to."""

    __tablename__ = "sellers"

    display_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    entity_type: Mapped[SellerEntityType] = mapped_column(
        Enum(SellerEntityType, name="seller_entity_type"),
        default=SellerEntityType.INDIVIDUAL,
        nullable=False,
    )
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    accounts: Mapped[list["SellerAccount"]] = relationship(
        back_populates="seller", cascade="all, delete-orphan"
    )


class SellerPlatform(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Identity.SellerPlatform — a marketplace/social channel (e.g. Facebook, Shopee, Line)."""

    __tablename__ = "seller_platforms"

    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    url_pattern: Mapped[str | None] = mapped_column(String(500), nullable=True)


class SellerAccount(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Identity.SellerAccount — a seller's specific handle/account on a platform."""

    __tablename__ = "seller_accounts"

    seller_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("sellers.id", ondelete="CASCADE"), nullable=False
    )
    platform_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("seller_platforms.id"), nullable=False
    )
    account_identifier: Mapped[str] = mapped_column(String(255), nullable=False)
    profile_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)

    seller: Mapped["Seller"] = relationship(back_populates="accounts")
    platform: Mapped["SellerPlatform"] = relationship()
