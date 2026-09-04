from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from app.db.base import get_db
from app.schemas.property import ProjectResponse, ProjectCreate
from app.api.deps import get_current_user, require_role
from app.crud.property import get_projects, get_project_by_slug, create_project

router = APIRouter()


@router.get("/", response_model=List[ProjectResponse])
async def list_projects(
    city_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    return await get_projects(db, city_id=city_id)


@router.get("/{slug}", response_model=ProjectResponse)
async def get_project(slug: str, db: AsyncSession = Depends(get_db)):
    project = await get_project_by_slug(db, slug)
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    return project


@router.post("/", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_new_project(
    project_data: ProjectCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_role("AGENT", "ADMIN")),
):
    return await create_project(db, project_data)
