from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import timedelta, datetime, timezone
from app.db.base import get_db
from app.schemas.user import UserCreate, UserResponse, Token, LoginRequest
from app.crud.user import create_user, authenticate_user, get_user_by_email
from app.core.security import create_access_token
from app.core.config import settings

router = APIRouter()
security = HTTPBearer()

# Simple in-memory rate limiter for login attempts
_login_attempts: dict[str, list[datetime]] = {}


def _rate_limited(email: str) -> None:
    now = datetime.now(timezone.utc)
    attempts = _login_attempts.get(email, [])
    attempts = [t for t in attempts if (now - t).total_seconds() < settings.LOGIN_RATE_WINDOW]
    if len(attempts) >= settings.LOGIN_RATE_LIMIT:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many login attempts. Please try again later.",
        )
    _login_attempts[email] = attempts


def _record_attempt(email: str) -> None:
    _login_attempts.setdefault(email, []).append(datetime.now(timezone.utc))


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate, db: AsyncSession = Depends(get_db)):
    # Check if user already exists
    existing_user = await get_user_by_email(db, email=user_data.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    # Always register as BUYER — roles are assigned by an admin
    user = await create_user(db, user_data, role="BUYER")
    return user


@router.post("/login", response_model=Token)
async def login(credentials: LoginRequest, db: AsyncSession = Depends(get_db)):
    email = credentials.email
    _rate_limited(email)

    user = await authenticate_user(db, email, credentials.password)
    if not user:
        _record_attempt(email)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email, "role": user.role}, expires_delta=access_token_expires
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user,
    }
