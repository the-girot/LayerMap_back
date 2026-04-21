from typing import Annotated
from fastapi import APIRouter, HTTPException, Path, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.dependencies import get_db, PaginationDep
from app.schemas.source import SourceCreate, SourceUpdate, SourceOut
from app.services import sources as svc
from app.services import projects as project_svc

router = APIRouter(prefix="/projects/{project_id}/sources", tags=["Sources"])


# ── Зависимость: загрузка проекта по project_id из пути ─────────
async def get_project(db: Annotated[AsyncSession, Depends(get_db)], project_id: Annotated[int, Path(...)]):
    project = await project_svc.get_one(db, project_id)
    if not project:
        raise HTTPException(404, "Проект не найден")
    return project


@router.get("", response_model=list[SourceOut])
@router.get("/", response_model=list[SourceOut])
async def list_sources(db: Annotated[AsyncSession, Depends(get_db)], project_id: Annotated[int, Path(...)]):
    project = await get_project(db, project_id)
    return await svc.get_list(db, project.id)


@router.get("/{source_id}", response_model=SourceOut)
async def get_source(source_id: int, db: Annotated[AsyncSession, Depends(get_db)], project_id: Annotated[int, Path(...)]):
    project = await get_project(db, project_id)
    obj = await svc.get_one(db, project.id, source_id)
    if not obj:
        raise HTTPException(404, "Источник не найден")
    return obj


@router.post("", response_model=SourceOut, status_code=201)
@router.post("/", response_model=SourceOut, status_code=201)
async def create_source(payload: SourceCreate, db: Annotated[AsyncSession, Depends(get_db)], project_id: Annotated[int, Path(...)]):
    project = await get_project(db, project_id)
    return await svc.create(db, project.id, payload)


@router.patch("/{source_id}", response_model=SourceOut)
async def update_source(
    source_id: int, payload: SourceUpdate, db: Annotated[AsyncSession, Depends(get_db)], project_id: Annotated[int, Path(...)]
):
    project = await get_project(db, project_id)
    obj = await svc.update(db, project.id, source_id, payload)
    if not obj:
        raise HTTPException(404, "Источник не найден")
    return obj


@router.delete("/{source_id}", status_code=204)
async def delete_source(source_id: int, db: Annotated[AsyncSession, Depends(get_db)], project_id: Annotated[int, Path(...)]):
    project = await get_project(db, project_id)
    deleted = await svc.delete(db, project.id, source_id)
    if not deleted:
        raise HTTPException(404, "Источник не найден")