from sqlalchemy import Column, String, Float, Integer, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base import Base
import enum


class PropertyType(str, enum.Enum):
    HOUSE = "HOUSE"
    APARTMENT = "APARTMENT"
    PLOT = "PLOT"
    COMMERCIAL = "COMMERCIAL"
    VILLA = "VILLA"
    FARM_HOUSE = "FARM_HOUSE"


class PropertyStatus(str, enum.Enum):
    FOR_SALE = "FOR_SALE"
    FOR_RENT = "FOR_RENT"
    SOLD = "SOLD"
    RENTED = "RENTED"


class ListingStatus(str, enum.Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    FEATURED = "FEATURED"


class City(Base):
    __tablename__ = "cities"
    
    id = Column(String, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    slug = Column(String, unique=True, nullable=False)
    province = Column(String, nullable=True)
    description = Column(String, nullable=True)
    image = Column(String, nullable=True)
    featured = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    properties = relationship("Property", back_populates="city")
    areas = relationship("Area", back_populates="city")


class Area(Base):
    __tablename__ = "areas"
    
    id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)
    slug = Column(String, nullable=False)
    city_id = Column(String, ForeignKey("cities.id"), nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    city = relationship("City", back_populates="areas")
    properties = relationship("Property", back_populates="area")


class Property(Base):
    __tablename__ = "properties"
    
    id = Column(String, primary_key=True, index=True)
    title = Column(String, nullable=False)
    slug = Column(String, unique=True, nullable=False)
    description = Column(Text, nullable=False)
    
    # Property Details
    type = Column(String, nullable=False)
    status = Column(String, nullable=False)
    listing_status = Column(String, default=ListingStatus.PENDING.value)
    
    # Location
    city_id = Column(String, ForeignKey("cities.id"), nullable=False)
    area_id = Column(String, ForeignKey("areas.id"), nullable=False)
    address = Column(String, nullable=False)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    
    # Pricing
    price = Column(Float, nullable=False)
    price_unit = Column(String, default="PKR")
    
    # Features
    bedrooms = Column(Integer, nullable=True)
    bathrooms = Column(Integer, nullable=True)
    kitchens = Column(Integer, nullable=True)
    area_size = Column(Float, nullable=False)
    area_unit = Column(String, default="sqft")
    
    # Building Details
    floor = Column(Integer, nullable=True)
    total_floors = Column(Integer, nullable=True)
    year_built = Column(Integer, nullable=True)
    furnished = Column(Boolean, default=False)
    
    # Amenities
    amenities = Column(String, nullable=True)  # JSON as string
    
    # Media
    video_url = Column(String, nullable=True)
    virtual_tour_url = Column(String, nullable=True)
    
    # Owner/Agent
    owner_id = Column(String, ForeignKey("users.id"), nullable=False)
    
    # Contact
    contact_phone = Column(String, nullable=True)
    contact_email = Column(String, nullable=True)
    
    # Stats
    views = Column(Integer, default=0)
    featured = Column(Boolean, default=False)
    
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    city = relationship("City", back_populates="properties")
    area = relationship("Area", back_populates="properties")
    owner = relationship("User", back_populates="properties")
    images = relationship("PropertyImage", back_populates="property")
    favorites = relationship("Favorite", back_populates="property")
    inquiries = relationship("Inquiry", back_populates="property")


class PropertyImage(Base):
    __tablename__ = "property_images"
    
    id = Column(String, primary_key=True, index=True)
    property_id = Column(String, ForeignKey("properties.id"), nullable=False)
    url = Column(String, nullable=False)
    caption = Column(String, nullable=True)
    is_primary = Column(Boolean, default=False)
    order = Column(Integer, default=0)
    created_at = Column(DateTime, server_default=func.now())
    
    # Relationships
    property = relationship("Property", back_populates="images")


class Favorite(Base):
    __tablename__ = "favorites"
    
    id = Column(String, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    property_id = Column(String, ForeignKey("properties.id"), nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="favorites")
    property = relationship("Property", back_populates="favorites")


class Inquiry(Base):
    __tablename__ = "inquiries"
    
    id = Column(String, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=True)
    property_id = Column(String, ForeignKey("properties.id"), nullable=False)
    name = Column(String, nullable=False)
    email = Column(String, nullable=False)
    phone = Column(String, nullable=True)
    message = Column(String, nullable=False)
    status = Column(String, default="PENDING")
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="inquiries")
    property = relationship("Property", back_populates="inquiries")
