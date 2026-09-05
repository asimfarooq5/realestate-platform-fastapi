from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, update
from sqlalchemy.orm import selectinload
from typing import List, Optional
from app.models.property import Property, PropertyImage, City, Area, Favorite, Inquiry, Project
from app.models.user import User
from app.schemas.property import PropertyCreate, PropertyUpdate, InquiryCreate, ProjectCreate
import uuid
import json
import math
from datetime import datetime


def _distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle distance between two points, in kilometers (haversine)."""
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    d_phi = math.radians(lat2 - lat1)
    d_lambda = math.radians(lon2 - lon1)
    a = math.sin(d_phi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(d_lambda / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


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
    agency_only: Optional[bool] = None,
    near_lat: Optional[float] = None,
    near_lng: Optional[float] = None,
) -> tuple[List[Property], int]:
    query = select(Property).where(Property.listing_status == "APPROVED")
    count_query = select(func.count(Property.id)).where(Property.listing_status == "APPROVED")

    if agency_only:
        # "Marketed by Malkiyat" — listings posted by verified agents/the
        # platform's own team, not ordinary owner-posted listings.
        agency_ids = select(User.id).where(User.role.in_(["AGENT", "ADMIN"]))
        query = query.where(Property.owner_id.in_(agency_ids))
        count_query = count_query.where(Property.owner_id.in_(agency_ids))
    
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
    
    query = query.options(
        selectinload(Property.images),
        selectinload(Property.city),
        selectinload(Property.area),
    )

    if near_lat is not None and near_lng is not None:
        # Small dataset: sort in Python by distance rather than reaching for
        # a DB-specific geo function. Listings with no coordinates sort last.
        query = query.order_by(Property.created_at.desc())
        result = await db.execute(query)
        all_properties = list(result.scalars().all())

        def sort_key(p: Property):
            if p.latitude is None or p.longitude is None:
                return (1, 0.0)
            return (0, _distance_km(near_lat, near_lng, p.latitude, p.longitude))

        all_properties.sort(key=sort_key)
        total = len(all_properties)
        return all_properties[skip : skip + limit], total

    query = query.offset(skip).limit(limit).order_by(Property.created_at.desc())

    result = await db.execute(query)
    properties = result.scalars().all()

    count_result = await db.execute(count_query)
    total = count_result.scalar()

    return list(properties), total


async def get_property_by_id(db: AsyncSession, property_id: str) -> Optional[Property]:
    result = await db.execute(
        select(Property)
        .where(Property.id == property_id)
        .options(
            selectinload(Property.images),
            selectinload(Property.city),
            selectinload(Property.area),
        )
    )
    return result.scalar_one_or_none()


async def get_property_by_slug(db: AsyncSession, slug: str) -> Optional[Property]:
    result = await db.execute(
        select(Property)
        .where(Property.slug == slug)
        .options(
            selectinload(Property.images),
            selectinload(Property.city),
            selectinload(Property.area),
        )
    )
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
        subtype=property_data.subtype,
        installments_available=property_data.installments_available,
        is_draft=property_data.is_draft,
        features=json.dumps(property_data.features) if property_data.features else None,
        amenities=json.dumps(property_data.amenities) if property_data.amenities else None,
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

    # Re-fetch with images/city/area eagerly loaded — PropertyResponse needs
    # them, and accessing an unloaded relationship after commit crashes with
    # MissingGreenlet (lazy-load isn't valid post-commit in an async session).
    return await get_property_by_id(db, db_property.id)


async def update_property(db: AsyncSession, property_id: str, property_update: PropertyUpdate) -> Optional[Property]:
    property_obj = await get_property_by_id(db, property_id)
    if not property_obj:
        return None
    
    update_data = property_update.model_dump(exclude_unset=True)
    if "amenities" in update_data and update_data["amenities"] is not None:
        update_data["amenities"] = json.dumps(update_data["amenities"])
    if "features" in update_data and update_data["features"] is not None:
        update_data["features"] = json.dumps(update_data["features"])
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
    await db.execute(
        update(Property)
        .where(Property.id == property_id)
        .values(views=Property.views + 1)
    )
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
async def create_inquiry(
    db: AsyncSession,
    inquiry_data: InquiryCreate,
    user_id: Optional[str] = None,
    property_id: Optional[str] = None,
) -> Inquiry:
    db_inquiry = Inquiry(
        id=str(uuid.uuid4()),
        user_id=user_id,
        property_id=property_id,
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


# User's own listings
async def get_user_properties(
    db: AsyncSession, owner_id: str, is_draft: Optional[bool] = None
) -> List[Property]:
    query = select(Property).where(Property.owner_id == owner_id)
    if is_draft is not None:
        query = query.where(Property.is_draft == is_draft)
    query = query.order_by(Property.created_at.desc()).options(
        selectinload(Property.images),
        selectinload(Property.city),
        selectinload(Property.area),
    )
    result = await db.execute(query)
    return list(result.scalars().all())


# Project CRUD
async def get_projects(db: AsyncSession, city_id: Optional[str] = None) -> List[Project]:
    query = select(Project).options(selectinload(Project.city))
    if city_id:
        query = query.where(Project.city_id == city_id)
    query = query.order_by(Project.created_at.desc())
    result = await db.execute(query)
    return list(result.scalars().all())


async def get_project_by_slug(db: AsyncSession, slug: str) -> Optional[Project]:
    result = await db.execute(
        select(Project).where(Project.slug == slug).options(selectinload(Project.city))
    )
    return result.scalar_one_or_none()


async def create_project(db: AsyncSession, project_data: ProjectCreate) -> Project:
    slug = project_data.title.lower().replace(" ", "-").replace("_", "-") + "-" + str(uuid.uuid4())[:8]
    db_project = Project(
        id=str(uuid.uuid4()),
        title=project_data.title,
        slug=slug,
        developer=project_data.developer,
        description=project_data.description,
        cover_image=project_data.cover_image,
        status=project_data.status.value,
        price_starting=project_data.price_starting,
        city_id=project_data.city_id,
    )
    db.add(db_project)
    await db.commit()
    await db.refresh(db_project)
    return db_project


# Favorites
async def get_favorites(db: AsyncSession, user_id: str) -> List[Favorite]:
    result = await db.execute(
        select(Favorite)
        .where(Favorite.user_id == user_id)
        .order_by(Favorite.created_at.desc())
        .options(selectinload(Favorite.property))
    )
    return list(result.scalars().all())
