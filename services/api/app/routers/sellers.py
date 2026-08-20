import uuid
from typing import Union

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_user_optional
from app.core.permissions import Role, effective_role
from app.database.session import get_db
from app.models.user import User
from app.schemas.seller import SellerCreate, SellerPublicRead, SellerRead
from app.services import seller_service

router = APIRouter(prefix="/sellers", tags=["sellers"])


@router.post("", response_model=SellerRead, status_code=status.HTTP_201_CREATED)
def create_seller(data: SellerCreate, db: Session = Depends(get_db)):
    return seller_service.create_seller(db, data)


@router.get("", response_model=list[Union[SellerRead, SellerPublicRead]])
def list_sellers(
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
):
    sellers = seller_service.list_sellers(db, skip=skip, limit=limit)
    if effective_role(current_user) == Role.PUBLIC:
        return [SellerPublicRead.from_seller(s) for s in sellers]
    return sellers


@router.get("/{seller_id}", response_model=Union[SellerRead, SellerPublicRead])
def get_seller(
    seller_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
):
    seller = seller_service.get_seller(db, seller_id)
    if seller is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Seller not found")
    if effective_role(current_user) == Role.PUBLIC:
        return SellerPublicRead.from_seller(seller)
    return seller
