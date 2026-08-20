import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.seller import SellerEntityType


class SellerBase(BaseModel):
    display_name: str
    entity_type: SellerEntityType = SellerEntityType.INDIVIDUAL
    description: str | None = None


class SellerCreate(SellerBase):
    pass


class SellerRead(SellerBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    created_at: datetime
    updated_at: datetime


class SellerPublicRead(BaseModel):
    """Public/anonymous view — identity fields (name) are masked.

    'Public สามารถเห็นโปรไฟล์ผู้ขายได้แต่จะไม่เห็นทั้งหมด (ชื่อ สกุล หน้าตา)'
    """

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    masked_name: str
    entity_type: SellerEntityType
    created_at: datetime

    @staticmethod
    def from_seller(seller) -> "SellerPublicRead":
        name = seller.display_name or ""
        visible = name[:2]
        masked = f"{visible}{'*' * max(len(name) - 2, 3)}" if name else "***"
        return SellerPublicRead(
            id=seller.id,
            masked_name=masked,
            entity_type=seller.entity_type,
            created_at=seller.created_at,
        )
