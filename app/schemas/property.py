from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from enum import Enum


class PropertyType(str, Enum):
    HOUSE = "HOUSE"
    APARTMENT = "APARTMENT"
    PLOT = "PLOT"
    COMMERCIAL = "COMMERCIAL"
    VILLA = "VILLA"
    FARM_HOUSE = "FARM_HOUSE"


class PropertyStatus(str, Enum):
    FOR_SALE = "FOR_SALE"
    FOR_RENT = "FOR_RENT"
    SOLD = "SOLD"
    RENTED = "RENTED"


class ListingStatus(str, Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    FEATURED = "FEATURED"


class CityBase(BaseModel):
    name: str
    slug: str
    province: Optional[str] = None
    description: Optional[str] = None
    image: Optional[str] = None
    featured: bool = False


class CityCreate(CityBase):
    pass


class CityInDB(CityBase):
    id: str
    created_at: datetime
    updated_at: datetime
    property_count: int = 0

    class Config:
        from_attributes = True


class CityResponse(CityInDB):
    pass


class AreaBase(BaseModel):
    name: str
    slug: str
    city_id: str


class AreaCreate(AreaBase):
    pass


class AreaInDB(AreaBase):
    id: str
    created_at: datetime
    updated_at: datetime
    property_count: int = 0

    class Config:
        from_attributes = True


class AreaResponse(AreaInDB):
    pass


class PropertyImageBase(BaseModel):
    url: str
    caption: Optional[str] = None
    is_primary: bool = False
    order: int = 0


class PropertyImageCreate(PropertyImageBase):
    property_id: str


class PropertyImageInDB(PropertyImageBase):
    id: str
    property_id: str
    created_at: datetime

    class Config:
        from_attributes = True


class PropertyImageResponse(PropertyImageInDB):
    pass


class PropertyBase(BaseModel):
    title: str
    description: str
    type: PropertyType
    status: PropertyStatus
    city_id: str
    area_id: str
    address: str
    price: float
    price_unit: str = "PKR"
    bedrooms: Optional[int] = None
    bathrooms: Optional[int] = None
    kitchens: Optional[int] = None
    area_size: float
    area_unit: str = "sqft"
    floor: Optional[int] = None
    total_floors: Optional[int] = None
    year_built: Optional[int] = None
    furnished: bool = False
    amenities: Optional[List[str]] = None
    video_url: Optional[str] = None
    virtual_tour_url: Optional[str] = None
    contact_phone: Optional[str] = None
    contact_email: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class PropertyCreate(PropertyBase):
    images: Optional[List[PropertyImageBase]] = None


class PropertyUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    status: Optional[PropertyStatus] = None
    listing_status: Optional[ListingStatus] = None
    featured: Optional[bool] = None


class PropertyInDB(PropertyBase):
    id: str
    slug: str
    listing_status: ListingStatus
    owner_id: str
    views: int
    featured: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PropertyResponse(PropertyInDB):
    images: List[PropertyImageResponse] = []
    city: Optional[CityResponse] = None
    area: Optional[AreaResponse] = None


class PropertyListResponse(BaseModel):
    properties: List[PropertyResponse]
    total: int
    page: int
    limit: int
    pages: int


class FavoriteBase(BaseModel):
    property_id: str


class FavoriteCreate(FavoriteBase):
    pass


class FavoriteInDB(FavoriteBase):
    id: str
    user_id: str
    created_at: datetime

    class Config:
        from_attributes = True


class InquiryBase(BaseModel):
    property_id: str
    name: str
    email: str
    phone: Optional[str] = None
    message: str


class InquiryCreate(InquiryBase):
    pass


class InquiryUpdate(BaseModel):
    status: Optional[str] = None


class InquiryInDB(InquiryBase):
    id: str
    user_id: Optional[str] = None
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class InquiryResponse(InquiryInDB):
    pass
