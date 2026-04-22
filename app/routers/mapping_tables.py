from fastapi import APIRouter, HTTPException

from app.core.dependencies import DBSession, ValidProject
from app.schemas.mapping_table import (
    MappingColumnCreate,
    MappingColumnOut,
    MappingColumnUpdate,
    MappingTableCreate,
    MappingTableOut,
    MappingTableUpdate,
)
from app.services import mapping_tables as svc

router = APIRouter(
    prefix="/projects/{project_id}/mapping-tables",
    tags=["Mapping Tables"],
)


# ── Таблицы ──────────────────────────────────────────────────────────────────
@router.get("", response_model=list[MappingTableOut])
@router.get("/", response_model=list[MappingTableOut])
async def list_mapping_tables(project: ValidProject, db: DBSession):
    return await svc.get_list(db, project.id)


@router.get("/{table_id}", response_model=MappingTableOut)
async def get_mapping_table(table_id: int, project: ValidProject, db: DBSession):
    obj = await svc.get_one(db, project.id, table_id)
    if not obj:
        raise HTTPException(404, "Таблица маппинга не найдена")
    return obj


@router.post("", response_model=MappingTableOut, status_code=201)
@router.post("/", response_model=MappingTableOut, status_code=201)
async def create_mapping_table(
    payload: MappingTableCreate, project: ValidProject, db: DBSession
):
    return await svc.create(db, project.id, payload)


@router.patch("/{table_id}", response_model=MappingTableOut)
async def update_mapping_table(
    table_id: int,
    payload: MappingTableUpdate,
    project: ValidProject,
    db: DBSession,
):
    obj = await svc.update(db, project.id, table_id, payload)
    if not obj:
        raise HTTPException(404, "Таблица маппинга не найдена")
    return obj


@router.delete("/{table_id}", status_code=204)
async def delete_mapping_table(table_id: int, project: ValidProject, db: DBSession):
    deleted = await svc.delete(db, project.id, table_id)
    if not deleted:
        raise HTTPException(404, "Таблица маппинга не найдена")


# ── Колонки ──────────────────────────────────────────────────────────────────


@router.get("/{table_id}/columns", response_model=list[MappingColumnOut])
async def list_columns(table_id: int, project: ValidProject, db: DBSession):
    table = await svc.get_one(db, project.id, table_id)
    if not table:
        raise HTTPException(404, "Таблица маппинга не найдена")
    return await svc.get_columns(db, table_id)


@router.get("/{table_id}/columns/{column_id}", response_model=MappingColumnOut)
async def get_column(
    table_id: int, column_id: int, project: ValidProject, db: DBSession
):
    # project проверяет принадлежность project_id; table — через get_column
    obj = await svc.get_column(db, table_id, column_id)
    if not obj:
        raise HTTPException(404, "Колонка не найдена")
    return obj


@router.post("/{table_id}/columns", response_model=MappingColumnOut, status_code=201)
async def create_column(
    table_id: int,
    payload: MappingColumnCreate,
    project: ValidProject,
    db: DBSession,
):
    table = await svc.get_one(db, project.id, table_id)
    if not table:
        raise HTTPException(404, "Таблица маппинга не найдена")
    return await svc.create_column(db, table_id, payload)


@router.patch("/{table_id}/columns/{column_id}", response_model=MappingColumnOut)
async def update_column(
    table_id: int,
    column_id: int,
    payload: MappingColumnUpdate,
    project: ValidProject,
    db: DBSession,
):
    obj = await svc.update_column(db, table_id, column_id, payload)
    if not obj:
        raise HTTPException(404, "Колонка не найдена")
    return obj


@router.delete("/{table_id}/columns/{column_id}", status_code=204)
async def delete_column(
    table_id: int, column_id: int, project: ValidProject, db: DBSession
):
    deleted = await svc.delete_column(db, table_id, column_id)
    if not deleted:
        raise HTTPException(404, "Колонка не найдена")
