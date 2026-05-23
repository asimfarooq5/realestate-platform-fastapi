from sqlalchemy import Column, String, DateTime, Enum as SQLEnum, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base import Base
import enum


class UserRole(str, enum.Enum):
    BUYER = "BUYER"
    SELLER = "SELLER"
    AGENT = "AGENT"
    ADMIN = "ADMIN"


class User(Base):
    __tablename__ = "users"
    
    id = Column(String, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password = Column(String, nullable=True)
    name = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    role = Column(String, default=UserRole.BUYER.value)
    image = Column(String, nullable=True)
    email_verified = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    properties = relationship("Property", back_populates="owner")
    favorites = relationship("Favorite", back_populates="user")
    inquiries = relationship("Inquiry", back_populates="user")
    agent_profile = relationship("AgentProfile", back_populates="user", uselist=False)


class AgentProfile(Base):
    __tablename__ = "agent_profiles"
    
    id = Column(String, primary_key=True, index=True)
    user_id = Column(String, unique=True, nullable=False)
    company_name = Column(String, nullable=True)
    license_number = Column(String, nullable=True)
    bio = Column(String, nullable=True)
    experience = Column(String, nullable=True)
    specialties = Column(String, nullable=True)  # JSON as string
    languages = Column(String, nullable=True)  # JSON as string
    verified = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="agent_profile")
