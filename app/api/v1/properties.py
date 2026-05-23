from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from app.db.base import get_db
from app.schemas.property import (
    PropertyCreate, PropertyResponse, PropertyUpdate, 
    PropertyListResponse, CityResponse, AreaResponse,
    InquiryCreate, InquiryResponse
)
from app.crud.property import (
    get_properties, get_property_by_id, get_property_by_slug,
    create_property, update_property, delete_property,
    increment_property_views, get_cities, get_areas_by_city,
    create_inquiry
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
    )
    
    pages = (total + limit - 1) // limit
    
    return {
        "properties": properties,
        "total": total,
        "page": page,
        "limit": limit,
        "pages": pages,
    }


@router.get("/{slug}", response_model=PropertyResponse)
async def get_property(slug: str, db: AsyncSession = Depends(get_db)):
    property_obj = await get_property_by_slug(db, slug)
    if not property_obj:
        raise HTTPException(status_code=404, detail="Property not found")
    
    # Increment views
    await increment_property_views(db, property_obj.id)
    
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
    
    inquiry = await create_inquiry(db, inquiry_data, current_user.id)
    return inquiry


# Cities and Areas
@router.get("/cities/list", response_model=List[CityResponse])
async def list_cities(db: AsyncSession = Depends(get_db)):
    cities = await get_cities(db)
    return cities


@router.get("/cities/{city_id}/areas", response_model=List[AreaResponse])
async def list_areas(city_id: str, db: AsyncSession = Depends(get_db)):
    areas = await get_areas_by_city(db, city_id)
    return areas
