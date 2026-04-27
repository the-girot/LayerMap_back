from fastapi import APIRouter, HTTPException

from app.core.auth import CurrentUser
from app.core.dependencies import ValidProject
from app.database import DBSession
from app.schemas.source_table import (
    SourceColumnCreate,
    SourceColumnOut,
    SourceColumnUpdate,
    SourceTableCreate,
    SourceTableOut,
    SourceTableUpdate,
)
from app.services import source_tables as svc
from app.services import sources as source_svc

router = APIRouter(
    prefix="/projects/{project_id}/sources/{source_id}/tables",
    tags=["Source Tables"],
)


# ── Таблицы ──────────────────────────────────────────────────────────────────
@router.get("", response_model=list[SourceTableOut])
@router.get("/", response_model=list[SourceTableOut])
async def list_source_tables(
    _: CurrentUser, source_id: int, project: ValidProject, db: DBSession
):
    src = await source_svc.get_one(db, project.id, source_id)
    if not src:
        raise HTTPException(404, "Источник не найден")
    return await svc.get_list(db, source_id)


@router.get("/{table_id}", response_model=SourceTableOut)
async def get_source_table(
    _: CurrentUser, source_id: int, table_id: int, project: ValidProject, db: DBSession
):
    obj = await svc.get_one(db, source_id, table_id)
    if not obj:
        raise HTTPException(404, "Таблица не найдена")
    return obj


@router.post("", response_model=SourceTableOut, status_code=201)
@router.post("/", response_model=SourceTableOut, status_code=201)
async def create_source_table(
    _: CurrentUser,
    source_id: int,
    payload: SourceTableCreate,
    project: ValidProject,
    db: DBSession,
):
    src = await source_svc.get_one(db, project.id, source_id)
    if not src:
        raise HTTPException(404, "Источник не найден")
    return await svc.create(db, source_id, payload)


@router.patch("/{table_id}", response_model=SourceTableOut)
async def update_source_table(
    _: CurrentUser,
    source_id: int,
    table_id: int,
    payload: SourceTableUpdate,
    project: ValidProject,
    db: DBSession,
):
    obj = await svc.update(db, source_id, table_id, payload)
    if not obj:
        raise HTTPException(404, "Таблица не найдена")
    return obj


@router.delete("/{table_id}", status_code=204)
async def delete_source_table(
    _: CurrentUser, source_id: int, table_id: int, project: ValidProject, db: DBSession
):
    deleted = await svc.delete(db, source_id, table_id)
    if not deleted:
        raise HTTPException(404, "Таблица не найдена")


# ── Колонки ──────────────────────────────────────────────────────────────────


@router.get("/{table_id}/columns", response_model=list[SourceColumnOut])
async def list_columns(
    _: CurrentUser, source_id: int, table_id: int, project: ValidProject, db: DBSession
):
    table = await svc.get_one(db, source_id, table_id)
    if not table:
        raise HTTPException(404, "Таблица не найдена")
    return await svc.get_columns(db, table_id)


@router.get("/{table_id}/columns/{column_id}", response_model=SourceColumnOut)
async def get_column(
    _: CurrentUser,
    source_id: int,
    table_id: int,
    column_id: int,
    project: ValidProject,
    db: DBSession,
):
    obj = await svc.get_column(db, table_id, column_id)
    if not obj:
        raise HTTPException(404, "Колонка не найдена")
    return obj


@router.post("/{table_id}/columns", response_model=SourceColumnOut, status_code=201)
async def create_column(
    _: CurrentUser,
    source_id: int,
    table_id: int,
    payload: SourceColumnCreate,
    project: ValidProject,
    db: DBSession,
):
    table = await svc.get_one(db, source_id, table_id)
    if not table:
        raise HTTPException(404, "Таблица не найдена")
    return await svc.create_column(db, table_id, payload)


@router.patch("/{table_id}/columns/{column_id}", response_model=SourceColumnOut)
async def update_column(
    _: CurrentUser,
    source_id: int,
    table_id: int,
    column_id: int,
    payload: SourceColumnUpdate,
    project: ValidProject,
    db: DBSession,
):
    obj = await svc.update_column(db, table_id, column_id, payload)
    if not obj:
        raise HTTPException(404, "Колонка не найдена")
    return obj


@router.delete("/{table_id}/columns/{column_id}", status_code=204)
async def delete_column(
    _: CurrentUser,
    source_id: int,
    table_id: int,
    column_id: int,
    project: ValidProject,
    db: DBSession,
):
    deleted = await svc.delete_column(db, table_id, column_id)
    if not deleted:
        raise HTTPException(404, "Колонка не найдена")
