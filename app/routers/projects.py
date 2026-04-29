from fastapi import APIRouter, HTTPException, Query

from app.core.auth import CurrentUser
from app.database import DBSession
from app.models.project import ProjectStatus
from app.schemas.project import (
    ProjectCreate,
    ProjectKPIOut,
    ProjectOut,
    ProjectSummaryOut,
    ProjectUpdate,
)
from app.services import projects as svc

router = APIRouter(prefix="/projects", tags=["Projects"])


@router.get("", response_model=list[ProjectOut])
@router.get("/", response_model=list[ProjectOut])
async def list_projects(
    db: DBSession,
    current_user: CurrentUser,
    status: ProjectStatus | None = Query(default=None),
    search: str | None = Query(default=None, min_length=1),
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
    sort_by: str = Query(default="updated_at"),
    sort_dir: str = Query(default="desc", pattern="^(asc|desc)$"),
):
    projects = await svc.get_filtered_list(
        db,
        status=status,
        search=search,
        page=page,
        size=size,
        sort_by=sort_by,
        sort_dir=sort_dir,
    )
    return [
        ProjectOut(
            id=p.id,
            name=p.name,
            description=p.description,
            status=p.status,
            created_at=p.created_at,
            updated_at=p.updated_at,
        )
        for p in projects
    ]


@router.get("/kpi", response_model=ProjectKPIOut)
async def get_projects_kpi(db: DBSession, current_user: CurrentUser):
    return await svc.get_kpi(db)


@router.get("/recent", response_model=list[ProjectSummaryOut])
async def get_recent_projects(
    db: DBSession,
    current_user: CurrentUser,
    limit: int = Query(5, ge=1, le=50),
):
    projects = await svc.get_recent(db, user_id=current_user.id, limit=limit)
    return [
        ProjectSummaryOut(
            id=p.id,
            name=p.name,
            status=p.status,
            updated_at=p.updated_at,
        )
        for p in projects
    ]


@router.get("/{project_id}", response_model=ProjectOut)
async def get_project(project_id: int, db: DBSession, current_user: CurrentUser):
    project = await svc.get_one(db, project_id)
    if not project:
        raise HTTPException(404, "Проект не найден")
    return ProjectOut(
        id=project.id,
        name=project.name,
        description=project.description,
        status=project.status,
        created_at=project.created_at,
        updated_at=project.updated_at,
    )


@router.post("", response_model=ProjectOut, status_code=201)
async def create_project(
    payload: ProjectCreate,
    db: DBSession,
    current_user: CurrentUser,
):
    obj = await svc.create(db, payload, user_id=current_user.id)
    return ProjectOut(
        id=obj.id,
        name=obj.name,
        description=obj.description,
        status=obj.status,
        created_at=obj.created_at,
        updated_at=obj.updated_at,
    )


@router.patch("/{project_id}", response_model=ProjectOut)
async def update_project(
    project_id: int,
    payload: ProjectUpdate,
    db: DBSession,
    current_user: CurrentUser,
):
    project = await svc.get_one(db, project_id)
    if not project:
        raise HTTPException(404, "Проект не найден")
    obj = await svc.update(db, project_id, payload)
    if not obj:
        raise HTTPException(404, "Проект не найден")
    return ProjectOut(
        id=obj.id,
        name=obj.name,
        description=obj.description,
        status=obj.status,
        created_at=obj.created_at,
        updated_at=obj.updated_at,
    )


@router.delete("/{project_id}", status_code=204)
async def delete_project(
    project_id: int,
    db: DBSession,
    current_user: CurrentUser,
):
    project = await svc.get_one(db, project_id)
    if not project:
        raise HTTPException(404, "Проект не найден")
    await svc.delete(db, project_id)
