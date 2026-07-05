"""Project CRUD endpoints (PRD §8.4)."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from axiom.core.database import get_db
from axiom.core.security import CurrentUser, get_current_user
from axiom.models.api_models import ProjectCreateRequest, ProjectOut
from axiom.models.db_models import Project

router = APIRouter(prefix="/projects", tags=["projects"])


@router.post("", response_model=ProjectOut, status_code=status.HTTP_201_CREATED)
async def create_project(
    body: ProjectCreateRequest,
    current: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ProjectOut:
    # Synthetic local principal has no users row — leave owner unset (FK-safe).
    owner_id = None if current.sub == "user:local" else current.sub.removeprefix("user:")
    project = Project(
        name=body.name,
        root_path=body.root_path,
        languages=body.languages,
        owner_id=owner_id,
    )
    db.add(project)
    await db.flush()
    return ProjectOut.model_validate(project)


@router.get("", response_model=list[ProjectOut])
async def list_projects(
    current: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[ProjectOut]:
    result = await db.execute(select(Project))
    return [ProjectOut.model_validate(p) for p in result.scalars().all()]


@router.get("/{project_id}", response_model=ProjectOut)
async def get_project(
    project_id: str,
    current: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ProjectOut:
    project = await db.get(Project, project_id)
    if project is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Project not found")
    return ProjectOut.model_validate(project)


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: str,
    current: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    project = await db.get(Project, project_id)
    if project is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Project not found")
    await db.delete(project)
