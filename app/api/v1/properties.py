from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List, Optional
from app.db.base import get_db
from app.models.property import City, Area, Property
from app.schemas.property import (
    PropertyCreate, PropertyResponse, PropertyUpdate,
    PropertyListResponse, CityResponse, AreaResponse,
    InquiryCreate, InquiryResponse, FavoriteResponse,
)
from app.crud.property import (
    get_properties, get_property_by_id, get_property_by_slug,
    create_property, update_property, delete_property,
    increment_property_views, get_cities, get_areas_by_city,
    create_inquiry, add_favorite, remove_favorite, get_favorites,
)
from app.api.deps import get_current_user

router = APIRouter()


@router.get("/", response_model=PropertyListResponse)
async def list_properties(
    page: int = Query(1, ge=1),
    limit: int = Query(12, ge=1, le=100),
    city_id: Optional[str] = None,
    area_id: Optional[str] = None,
    type: Optional[str] = None,
    status: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    bedrooms: Optional[int] = None,
    search: Optional[str] = None,
    featured: Optional[bool] = None,
    near_lat: Optional[float] = None,
    near_lng: Optional[float] = None,
    db: AsyncSession = Depends(get_db),
):
    skip = (page - 1) * limit
    properties, total = await get_properties(
        db, skip=skip, limit=limit,
        city_id=city_id, area_id=area_id,
        property_type=type, status=status,
        min_price=min_price, max_price=max_price,
        bedrooms=bedrooms, search=search,
        featured=featured,
        near_lat=near_lat, near_lng=near_lng,
    )

    pages = (total + limit - 1) // limit

    return {
        "properties": properties,
        "total": total,
        "page": page,
        "limit": limit,
        "pages": pages,
    }


# Cities and Areas — MUST be declared before the dynamic /{slug} route
@router.get("/cities/list", response_model=List[CityResponse])
async def list_cities(db: AsyncSession = Depends(get_db)):
    # Query cities with an aggregated APPROVED property count
    result = await db.execute(
        select(
            City,
            func.count(Property.id).filter(Property.listing_status == "APPROVED").label("property_count"),
        )
        .outerjoin(Property, Property.city_id == City.id)
        .group_by(City.id)
        .order_by(City.name)
    )
    rows = result.all()
    cities = []
    for city, count in rows:
        cities.append(CityResponse(
            id=city.id,
            name=city.name,
            slug=city.slug,
            province=city.province,
            description=city.description,
            image=city.image,
            featured=city.featured,
            created_at=city.created_at,
            updated_at=city.updated_at,
            property_count=count or 0,
        ))
    return cities


@router.get("/cities/{city_id}/areas", response_model=List[AreaResponse])
async def list_areas(city_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(
            Area,
            func.count(Property.id).filter(Property.listing_status == "APPROVED").label("property_count"),
        )
        .outerjoin(Property, Property.area_id == Area.id)
        .where(Area.city_id == city_id)
        .group_by(Area.id)
        .order_by(Area.name)
    )
    rows = result.all()
    areas = []
    for area, count in rows:
        areas.append(AreaResponse(
            id=area.id,
            name=area.name,
            slug=area.slug,
            city_id=area.city_id,
            created_at=area.created_at,
            updated_at=area.updated_at,
            property_count=count or 0,
        ))
    return areas


@router.get("/{slug}", response_model=PropertyResponse)
async def get_property(slug: str, db: AsyncSession = Depends(get_db)):
    property_obj = await get_property_by_slug(db, slug)
    if not property_obj:
        raise HTTPException(status_code=404, detail="Property not found")

    # Increment views (bulk update) then refresh to re-sync the ORM instance
    await increment_property_views(db, property_obj.id)
    await db.refresh(property_obj)

    return property_obj


@router.post("/", response_model=PropertyResponse, status_code=status.HTTP_201_CREATED)
async def create_new_property(
    property_data: PropertyCreate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
):
    # Check if user is agent, seller, or admin
    if current_user.role not in ["AGENT", "SELLER", "ADMIN"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only agents and sellers can create properties",
        )

    property_obj = await create_property(db, property_data, current_user.id)
    return property_obj


@router.put("/{property_id}", response_model=PropertyResponse)
async def update_existing_property(
    property_id: str,
    property_update: PropertyUpdate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
):
    property_obj = await get_property_by_id(db, property_id)
    if not property_obj:
        raise HTTPException(status_code=404, detail="Property not found")

    # Check ownership or admin
    if property_obj.owner_id != current_user.id and current_user.role != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this property",
        )

    updated_property = await update_property(db, property_id, property_update)
    return updated_property


@router.delete("/{property_id}")
async def delete_existing_property(
    property_id: str,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
):
    property_obj = await get_property_by_id(db, property_id)
    if not property_obj:
        raise HTTPException(status_code=404, detail="Property not found")

    # Check ownership or admin
    if property_obj.owner_id != current_user.id and current_user.role != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this property",
        )

    success = await delete_property(db, property_id)
    if success:
        return {"message": "Property deleted successfully"}
    raise HTTPException(status_code=500, detail="Failed to delete property")


@router.post("/{property_id}/inquiry", response_model=InquiryResponse)
async def create_property_inquiry(
    property_id: str,
    inquiry_data: InquiryCreate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
):
    property_obj = await get_property_by_id(db, property_id)
    if not property_obj:
        raise HTTPException(status_code=404, detail="Property not found")

    # Use the property_id from the URL, not the body
    inquiry = await create_inquiry(db, inquiry_data, current_user.id, property_id)
    return inquiry


# Favorites
@router.post("/{property_id}/favorite", response_model=FavoriteResponse)
async def add_property_favorite(
    property_id: str,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
):
    property_obj = await get_property_by_id(db, property_id)
    if not property_obj:
        raise HTTPException(status_code=404, detail="Property not found")

    try:
        favorite = await add_favorite(db, current_user.id, property_id)
        return favorite
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Property already in favorites",
        )


@router.delete("/{property_id}/favorite")
async def remove_property_favorite(
    property_id: str,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
):
    success = await remove_favorite(db, current_user.id, property_id)
    if not success:
        raise HTTPException(status_code=404, detail="Favorite not found")
    return {"message": "Removed from favorites"}


@router.get("/{property_id}/favorite/status", response_model=bool)
async def get_favorite_status(
    property_id: str,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
):
    favorites = await get_favorites(db, current_user.id)
    return any(f.property_id == property_id for f in favorites)
