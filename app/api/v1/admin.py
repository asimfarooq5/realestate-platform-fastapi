from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from typing import List, Optional
from app.db.base import get_db
from app.schemas.property import (
    PropertyResponse, InquiryResponse, InquiryInDB, PropertyUpdate, PropertyModeration,
)
from app.schemas.user import UserResponse, UserRoleUpdate
from app.crud.property import get_property_by_id
from app.api.deps import require_role
from app.models.property import Property, Inquiry
from app.models.user import User

router = APIRouter(dependencies=[Depends(require_role("ADMIN"))])


@router.get("/properties", response_model=List[PropertyResponse])
async def list_all_properties(
    listing_status: Optional[str] = Query(None, description="Filter by PENDING/APPROVED/REJECTED/FEATURED"),
    db: AsyncSession = Depends(get_db),
):
    query = select(Property).order_by(Property.created_at.desc())
    if listing_status:
        query = query.where(Property.listing_status == listing_status.upper())
    query = query.options(
        selectinload(Property.images),
        selectinload(Property.city),
        selectinload(Property.area),
    )
    result = await db.execute(query)
    return list(result.scalars().all())


@router.put("/properties/{property_id}/moderation", response_model=PropertyResponse)
async def moderate_property(
    property_id: str,
    moderation: PropertyModeration,
    db: AsyncSession = Depends(get_db),
):
    property_obj = await get_property_by_id(db, property_id)
    if not property_obj:
        raise HTTPException(status_code=404, detail="Property not found")

    data = moderation.model_dump(exclude_unset=True)
    for field, value in data.items():
        if value is not None:
            setattr(property_obj, field, value)
    await db.commit()
    await db.refresh(property_obj)
    return property_obj


@router.get("/inquiries", response_model=List[InquiryResponse])
async def list_all_inquiries(
    status_filter: Optional[str] = Query(None, alias="status"),
    db: AsyncSession = Depends(get_db),
):
    query = select(Inquiry).order_by(Inquiry.created_at.desc()).options(selectinload(Inquiry.property))
    if status_filter:
        query = query.where(Inquiry.status == status_filter.upper())
    result = await db.execute(query)
    inquiries = list(result.scalars().all())
    return [
        InquiryResponse(
            **InquiryInDB.model_validate(inquiry).model_dump(),
            property_title=inquiry.property.title if inquiry.property else None,
            property_slug=inquiry.property.slug if inquiry.property else None,
        )
        for inquiry in inquiries
    ]


@router.get("/users", response_model=List[UserResponse])
async def list_all_users(
    role: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    query = select(User).order_by(User.created_at.desc())
    if role:
        query = query.where(User.role == role.upper())
    result = await db.execute(query)
    return list(result.scalars().all())


@router.put("/users/{user_id}/role", response_model=UserResponse)
async def update_user_role(
    user_id: str,
    role_update: UserRoleUpdate,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.role = role_update.role.value
    await db.commit()
    await db.refresh(user)
    return user
