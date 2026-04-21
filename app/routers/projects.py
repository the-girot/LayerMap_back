from typing import Optional
from fastapi import APIRouter, Query, HTTPException
from app.core.dependencies import DBSession, ValidProject, PaginationDep
from app.schemas.project import ProjectCreate, ProjectUpdate, ProjectOut
from app.services import projects as svc

router = APIRouter(prefix="/projects", tags=["Projects"])


@router.get("", response_model=list[ProjectOut])
@router.get("/", response_model=list[ProjectOut])
async def list_projects(db: DBSession):
    projects = await svc.get_list(db)
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


@router.get("/{project_id}", response_model=ProjectOut)
async def get_project(project: ValidProject) -> ProjectOut:
    return ProjectOut(
        id=project.id,
        name=project.name,
        description=project.description,
        status=project.status,
        created_at=project.created_at,
        updated_at=project.updated_at,
    )


@router.post("", response_model=ProjectOut, status_code=201)
@router.post("/", response_model=ProjectOut, status_code=201)
async def create_project(payload: ProjectCreate, db: DBSession):
    obj = await svc.create(db, payload)
    return ProjectOut(
        id=obj.id,
        name=obj.name,
        description=obj.description,
        status=obj.status,
        created_at=obj.created_at,
        updated_at=obj.updated_at,
    )


@router.patch("/{project_id}", response_model=ProjectOut)
async def update_project(payload: ProjectUpdate, project: ValidProject, db: DBSession):
    obj = await svc.update(db, project.id, payload)
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
async def delete_project(project: ValidProject, db: DBSession):
    await svc.delete(db, project.id)