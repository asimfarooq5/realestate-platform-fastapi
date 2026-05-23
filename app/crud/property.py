from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from typing import List, Optional
from app.models.property import Property, PropertyImage, City, Area, Favorite, Inquiry
from app.schemas.property import PropertyCreate, PropertyUpdate, InquiryCreate
import uuid
from datetime import datetime


async def get_properties(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 12,
    city_id: Optional[str] = None,
    area_id: Optional[str] = None,
    property_type: Optional[str] = None,
    status: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    bedrooms: Optional[int] = None,
    search: Optional[str] = None,
    featured: Optional[bool] = None,
) -> tuple[List[Property], int]:
    query = select(Property).where(Property.listing_status == "APPROVED")
    count_query = select(func.count(Property.id)).where(Property.listing_status == "APPROVED")
    
    if city_id:
        query = query.where(Property.city_id == city_id)
        count_query = count_query.where(Property.city_id == city_id)
    
    if area_id:
        query = query.where(Property.area_id == area_id)
        count_query = count_query.where(Property.area_id == area_id)
    
    if property_type:
        query = query.where(Property.type == property_type)
        count_query = count_query.where(Property.type == property_type)
    
    if status:
        query = query.where(Property.status == status)
        count_query = count_query.where(Property.status == status)
    
    if min_price is not None:
        query = query.where(Property.price >= min_price)
        count_query = count_query.where(Property.price >= min_price)
    
    if max_price is not None:
        query = query.where(Property.price <= max_price)
        count_query = count_query.where(Property.price <= max_price)
    
    if bedrooms is not None:
        query = query.where(Property.bedrooms == bedrooms)
        count_query = count_query.where(Property.bedrooms == bedrooms)
    
    if featured is not None:
        query = query.where(Property.featured == featured)
        count_query = count_query.where(Property.featured == featured)
    
    if search:
        search_filter = or_(
            Property.title.ilike(f"%{search}%"),
            Property.description.ilike(f"%{search}%"),
            Property.address.ilike(f"%{search}%"),
        )
        query = query.where(search_filter)
        count_query = count_query.where(search_filter)
    
    query = query.offset(skip).limit(limit).order_by(Property.created_at.desc())
    
    result = await db.execute(query)
    properties = result.scalars().all()
    
    count_result = await db.execute(count_query)
    total = count_result.scalar()
    
    return list(properties), total


async def get_property_by_id(db: AsyncSession, property_id: str) -> Optional[Property]:
    result = await db.execute(select(Property).where(Property.id == property_id))
    return result.scalar_one_or_none()


async def get_property_by_slug(db: AsyncSession, slug: str) -> Optional[Property]:
    result = await db.execute(select(Property).where(Property.slug == slug))
    return result.scalar_one_or_none()


async def create_property(db: AsyncSession, property_data: PropertyCreate, owner_id: str) -> Property:
    slug = property_data.title.lower().replace(" ", "-").replace("_", "-") + "-" + str(uuid.uuid4())[:8]
    
    db_property = Property(
        id=str(uuid.uuid4()),
        title=property_data.title,
        slug=slug,
        description=property_data.description,
        type=property_data.type.value,
        status=property_data.status.value,
        listing_status="PENDING",
        city_id=property_data.city_id,
        area_id=property_data.area_id,
        address=property_data.address,
        price=property_data.price,
        price_unit=property_data.price_unit,
        bedrooms=property_data.bedrooms,
        bathrooms=property_data.bathrooms,
        kitchens=property_data.kitchens,
        area_size=property_data.area_size,
        area_unit=property_data.area_unit,
        floor=property_data.floor,
        total_floors=property_data.total_floors,
        year_built=property_data.year_built,
        furnished=property_data.furnished,
        amenities=str(property_data.amenities) if property_data.amenities else None,
        video_url=property_data.video_url,
        virtual_tour_url=property_data.virtual_tour_url,
        contact_phone=property_data.contact_phone,
        contact_email=property_data.contact_email,
        latitude=property_data.latitude,
        longitude=property_data.longitude,
        owner_id=owner_id,
    )
    db.add(db_property)
    await db.commit()
    await db.refresh(db_property)
    
    # Add images if provided
    if property_data.images:
        for idx, img in enumerate(property_data.images):
            db_image = PropertyImage(
                id=str(uuid.uuid4()),
                property_id=db_property.id,
                url=img.url,
                caption=img.caption,
                is_primary=img.is_primary or idx == 0,
                order=img.order or idx,
            )
            db.add(db_image)
        await db.commit()
    
    return db_property


async def update_property(db: AsyncSession, property_id: str, property_update: PropertyUpdate) -> Optional[Property]:
    property_obj = await get_property_by_id(db, property_id)
    if not property_obj:
        return None
    
    update_data = property_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(property_obj, field, value)
    
    await db.commit()
    await db.refresh(property_obj)
    return property_obj


async def delete_property(db: AsyncSession, property_id: str) -> bool:
    property_obj = await get_property_by_id(db, property_id)
    if not property_obj:
        return False
    
    await db.delete(property_obj)
    await db.commit()
    return True


async def increment_property_views(db: AsyncSession, property_id: str) -> None:
    property_obj = await get_property_by_id(db, property_id)
    if property_obj:
        property_obj.views += 1
        await db.commit()


# City CRUD
async def get_cities(db: AsyncSession) -> List[City]:
    result = await db.execute(select(City).order_by(City.name))
    return list(result.scalars().all())


async def get_city_by_id(db: AsyncSession, city_id: str) -> Optional[City]:
    result = await db.execute(select(City).where(City.id == city_id))
    return result.scalar_one_or_none()


async def get_areas_by_city(db: AsyncSession, city_id: str) -> List[Area]:
    result = await db.execute(select(Area).where(Area.city_id == city_id).order_by(Area.name))
    return list(result.scalars().all())


# Favorites CRUD
async def add_favorite(db: AsyncSession, user_id: str, property_id: str) -> Favorite:
    db_favorite = Favorite(
        id=str(uuid.uuid4()),
        user_id=user_id,
        property_id=property_id,
    )
    db.add(db_favorite)
    await db.commit()
    await db.refresh(db_favorite)
    return db_favorite


async def remove_favorite(db: AsyncSession, user_id: str, property_id: str) -> bool:
    result = await db.execute(
        select(Favorite).where(Favorite.user_id == user_id, Favorite.property_id == property_id)
    )
    favorite = result.scalar_one_or_none()
    if favorite:
        await db.delete(favorite)
        await db.commit()
        return True
    return False


# Inquiry CRUD
async def create_inquiry(db: AsyncSession, inquiry_data: InquiryCreate, user_id: Optional[str] = None) -> Inquiry:
    db_inquiry = Inquiry(
        id=str(uuid.uuid4()),
        user_id=user_id,
        property_id=inquiry_data.property_id,
        name=inquiry_data.name,
        email=inquiry_data.email,
        phone=inquiry_data.phone,
        message=inquiry_data.message,
        status="PENDING",
    )
    db.add(db_inquiry)
    await db.commit()
    await db.refresh(db_inquiry)
    return db_inquiry
