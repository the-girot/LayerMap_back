from typing import Annotated
from fastapi import APIRouter, HTTPException, Path, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.dependencies import get_db
from app.schemas.mapping_table import (
    MappingTableCreate, MappingTableUpdate, MappingTableOut,
    MappingColumnCreate, MappingColumnUpdate, MappingColumnOut,
)
from app.services import mapping_tables as svc
from app.services import projects as project_svc

router = APIRouter(prefix="/projects/{project_id}/mapping-tables", tags=["Mapping Tables"])


# ── Зависимость: загрузка проекта по project_id из пути ─────────
async def get_project(db: Annotated[AsyncSession, Depends(get_db)], project_id: Annotated[int, Path(...)]):
    project = await project_svc.get_one(db, project_id)
    if not project:
        raise HTTPException(404, "Проект не найден")
    return project


# ── Таблицы ───────────────────────────────────────────────────
@router.get("", response_model=list[MappingTableOut])
@router.get("/", response_model=list[MappingTableOut])
async def list_mapping_tables(db: Annotated[AsyncSession, Depends(get_db)], project_id: Annotated[int, Path(...)]):
    project = await get_project(db, project_id)
    return await svc.get_list(db, project.id)


@router.get("/{table_id}", response_model=MappingTableOut)
async def get_mapping_table(table_id: int, db: Annotated[AsyncSession, Depends(get_db)], project_id: Annotated[int, Path(...)]):
    project = await get_project(db, project_id)
    obj = await svc.get_one(db, project.id, table_id)
    if not obj:
        raise HTTPException(404, "Таблица маппинга не найдена")
    return obj


@router.post("", response_model=MappingTableOut, status_code=201)
@router.post("/", response_model=MappingTableOut, status_code=201)
async def create_mapping_table(
    payload: MappingTableCreate, db: Annotated[AsyncSession, Depends(get_db)], project_id: Annotated[int, Path(...)]
):
    project = await get_project(db, project_id)
    return await svc.create(db, project.id, payload)


@router.patch("/{table_id}", response_model=MappingTableOut)
async def update_mapping_table(
    table_id: int, payload: MappingTableUpdate, db: Annotated[AsyncSession, Depends(get_db)], project_id: Annotated[int, Path(...)]
):
    project = await get_project(db, project_id)
    obj = await svc.update(db, project.id, table_id, payload)
    if not obj:
        raise HTTPException(404, "Таблица маппинга не найдена")
    return obj


@router.delete("/{table_id}", status_code=204)
async def delete_mapping_table(table_id: int, db: Annotated[AsyncSession, Depends(get_db)], project_id: Annotated[int, Path(...)]):
    project = await get_project(db, project_id)
    deleted = await svc.delete(db, project.id, table_id)
    if not deleted:
        raise HTTPException(404, "Таблица маппинга не найдена")


# ── Колонки ───────────────────────────────────────────────────
@router.get("/{table_id}/columns", response_model=list[MappingColumnOut])
async def list_columns(table_id: int, db: Annotated[AsyncSession, Depends(get_db)], project_id: Annotated[int, Path(...)]):
    project = await get_project(db, project_id)
    await svc.get_one(db, project.id, table_id) or (_ for _ in ()).throw(
        HTTPException(404, "Таблица маппинга не найдена")
    )
    return await svc.get_columns(db, table_id)


@router.get("/{table_id}/columns/{column_id}", response_model=MappingColumnOut)
async def get_column(table_id: int, column_id: int, db: Annotated[AsyncSession, Depends(get_db)], project_id: Annotated[int, Path(...)]):
    project = await get_project(db, project_id)
    obj = await svc.get_column(db, table_id, column_id)
    if not obj:
        raise HTTPException(404, "Колонка не найдена")
    return obj


@router.post("/{table_id}/columns", response_model=MappingColumnOut, status_code=201)
async def create_column(
    table_id: int, payload: MappingColumnCreate, db: Annotated[AsyncSession, Depends(get_db)], project_id: Annotated[int, Path(...)]
):
    project = await get_project(db, project_id)
    table = await svc.get_one(db, project.id, table_id)
    if not table:
        raise HTTPException(404, "Таблица маппинга не найдена")
    return await svc.create_column(db, table_id, payload)


@router.patch("/{table_id}/columns/{column_id}", response_model=MappingColumnOut)
async def update_column(
    table_id: int, column_id: int, payload: MappingColumnUpdate,
    db: Annotated[AsyncSession, Depends(get_db)], project_id: Annotated[int, Path(...)],
):
    project = await get_project(db, project_id)
    obj = await svc.update_column(db, table_id, column_id, payload)
    if not obj:
        raise HTTPException(404, "Колонка не найдена")
    return obj


@router.delete("/{table_id}/columns/{column_id}", status_code=204)
async def delete_column(
    table_id: int, column_id: int, db: Annotated[AsyncSession, Depends(get_db)], project_id: Annotated[int, Path(...)]
):
    project = await get_project(db, project_id)
    deleted = await svc.delete_column(db, table_id, column_id)
    if not deleted:
        raise HTTPException(404, "Колонка не найдена")