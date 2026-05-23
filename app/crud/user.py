from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional
from app.models.user import User, AgentProfile
from app.schemas.user import UserCreate, UserUpdate, AgentProfileCreate
from app.core.security import get_password_hash, verify_password
import uuid


async def get_user_by_email(db: AsyncSession, email: str) -> Optional[User]:
    result = await db.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


async def get_user_by_id(db: AsyncSession, user_id: str) -> Optional[User]:
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


async def create_user(db: AsyncSession, user: UserCreate) -> User:
    db_user = User(
        id=str(uuid.uuid4()),
        email=user.email,
        password=get_password_hash(user.password),
        name=user.name,
        phone=user.phone,
        role=user.role.value,
        image=user.image,
    )
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user


async def authenticate_user(db: AsyncSession, email: str, password: str) -> Optional[User]:
    user = await get_user_by_email(db, email)
    if not user:
        return None
    if not verify_password(password, user.password):
        return None
    return user


async def update_user(db: AsyncSession, user_id: str, user_update: UserUpdate) -> Optional[User]:
    user = await get_user_by_id(db, user_id)
    if not user:
        return None
    
    update_data = user_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(user, field, value)
    
    await db.commit()
    await db.refresh(user)
    return user


async def create_agent_profile(db: AsyncSession, user_id: str, profile: AgentProfileCreate) -> AgentProfile:
    db_profile = AgentProfile(
        id=str(uuid.uuid4()),
        user_id=user_id,
        company_name=profile.company_name,
        license_number=profile.license_number,
        bio=profile.bio,
        experience=str(profile.experience) if profile.experience else None,
        specialties=str(profile.specialties) if profile.specialties else None,
        languages=str(profile.languages) if profile.languages else None,
        verified=profile.verified,
    )
    db.add(db_profile)
    await db.commit()
    await db.refresh(db_profile)
    return db_profile
