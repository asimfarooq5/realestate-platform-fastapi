from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.db.base import get_db
from app.api.deps import require_role
from app.schemas.chat import CommunityPostCreate, CommunityPostResponse
from app.crud.chat import list_community_posts, create_community_post

router = APIRouter()


@router.get("/posts", response_model=List[CommunityPostResponse])
async def get_community_posts(db: AsyncSession = Depends(get_db)):
    return await list_community_posts(db)


@router.post("/posts", response_model=CommunityPostResponse, status_code=201)
async def create_post(
    post_data: CommunityPostCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_role("ADMIN")),
):
    return await create_community_post(db, post_data, current_user.id)
