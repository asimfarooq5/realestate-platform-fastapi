from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime
from enum import Enum


class UserRole(str, Enum):
    BUYER = "BUYER"
    SELLER = "SELLER"
    AGENT = "AGENT"
    ADMIN = "ADMIN"


class UserBase(BaseModel):
    email: EmailStr
    name: Optional[str] = None
    phone: Optional[str] = None
    image: Optional[str] = None


class UserCreate(UserBase):
    password: str
    role: UserRole = UserRole.BUYER


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class UserRoleUpdate(BaseModel):
    role: UserRole


class UserUpdate(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    image: Optional[str] = None


class UserInDB(UserBase):
    id: str
    role: UserRole = UserRole.BUYER
    email_verified: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class UserResponse(UserInDB):
    pass


class AgentProfileBase(BaseModel):
    company_name: Optional[str] = None
    license_number: Optional[str] = None
    bio: Optional[str] = None
    experience: Optional[int] = None
    specialties: Optional[List[str]] = None
    languages: Optional[List[str]] = None
    verified: bool = False


class AgentProfileCreate(AgentProfileBase):
    pass


class AgentProfileUpdate(AgentProfileBase):
    pass


class AgentProfileInDB(AgentProfileBase):
    id: str
    user_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AgentProfileResponse(AgentProfileInDB):
    pass


class Token(BaseModel):
    access_token: str
    token_type: str
    user: Optional[UserResponse] = None


class TokenData(BaseModel):
    email: Optional[str] = None
