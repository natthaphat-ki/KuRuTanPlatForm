import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.seller import Seller
from app.schemas.seller import SellerCreate


def create_seller(db: Session, data: SellerCreate) -> Seller:
    seller = Seller(**data.model_dump())
    db.add(seller)
    db.commit()
    db.refresh(seller)
    return seller


def list_sellers(db: Session, skip: int = 0, limit: int = 50) -> list[Seller]:
    return list(db.execute(select(Seller).offset(skip).limit(limit)).scalars())


def get_seller(db: Session, seller_id: uuid.UUID) -> Seller | None:
    return db.get(Seller, seller_id)
