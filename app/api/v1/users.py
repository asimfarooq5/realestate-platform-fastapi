from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from typing import List, Optional
from app.db.base import get_db
from app.schemas.property import PropertyResponse, InquiryResponse, InquiryInDB
from app.schemas.user import UserResponse, UserUpdate
from app.api.deps import get_current_user
from app.crud.property import get_user_properties
from app.crud.user import update_user, deactivate_user
from app.models.property import Property, Inquiry
from app.models.property import Favorite as FavoriteModel

router = APIRouter()


@router.get("/me", response_model=UserResponse)
async def get_my_profile(
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
):
    return current_user


@router.put("/me", response_model=UserResponse)
async def update_my_profile(
    update_data: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
):
    return await update_user(db, current_user.id, update_data)


@router.post("/me/deactivate", status_code=status.HTTP_204_NO_CONTENT)
async def deactivate_my_account(
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
):
    await deactivate_user(db, current_user.id)


@router.get("/me/favorites", response_model=List[PropertyResponse])
async def get_my_favorites(
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
):
    result = await db.execute(
        select(FavoriteModel)
        .where(FavoriteModel.user_id == current_user.id)
        .order_by(FavoriteModel.created_at.desc())
        .options(
            selectinload(FavoriteModel.property).selectinload(Property.images),
            selectinload(FavoriteModel.property).selectinload(Property.city),
            selectinload(FavoriteModel.property).selectinload(Property.area),
        )
    )
    favorites = list(result.scalars().all())
    return [fav.property for fav in favorites if fav.property]


@router.get("/me/inquiries", response_model=List[InquiryResponse])
async def get_my_inquiries(
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
):
    result = await db.execute(
        select(Inquiry)
        .where(Inquiry.user_id == current_user.id)
        .order_by(Inquiry.created_at.desc())
        .options(selectinload(Inquiry.property))
    )
    inquiries = list(result.scalars().all())
    return [
        InquiryResponse(
            **InquiryInDB.model_validate(inquiry).model_dump(),
            property_title=inquiry.property.title if inquiry.property else None,
            property_slug=inquiry.property.slug if inquiry.property else None,
        )
        for inquiry in inquiries
    ]


@router.get("/me/properties", response_model=List[PropertyResponse])
async def get_my_properties(
    is_draft: Optional[bool] = None,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """All of the current user's own listings. Pass is_draft=true for the
    Drafts screen, is_draft=false for published/pending listings."""
    return await get_user_properties(db, current_user.id, is_draft=is_draft)
