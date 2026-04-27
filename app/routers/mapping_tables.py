from fastapi import APIRouter, HTTPException
from sqlalchemy import select

from app.core.auth import CurrentUser
from app.core.dependencies import ValidProject
from app.database import DBSession
from app.models.mapping_table import MappingColumn
from app.schemas.mapping_table import (
    MappingColumnCreate,
    MappingColumnOut,
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
async def list_mapping_tables(_: CurrentUser, project: ValidProject, db: DBSession):
    return await svc.get_list(db, project.id)


@router.get("/{table_id}", response_model=MappingTableOut)
async def get_mapping_table(
    _: CurrentUser, table_id: int, project: ValidProject, db: DBSession
):
    obj = await svc.get_one(db, project.id, table_id)
    if not obj:
        raise HTTPException(404, "Таблица маппинга не найдена")
    return obj


@router.post("", response_model=MappingTableOut, status_code=201)
@router.post("/", response_model=MappingTableOut, status_code=201)
async def create_mapping_table(
    _: CurrentUser,
    payload: MappingTableCreate,
    project: ValidProject,
    db: DBSession,
):
    return await svc.create(db, project.id, payload)


@router.patch("/{table_id}", response_model=MappingTableOut)
async def update_mapping_table(
    _: CurrentUser,
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
async def delete_mapping_table(
    _: CurrentUser, table_id: int, project: ValidProject, db: DBSession
):
    deleted = await svc.delete(db, project.id, table_id)
    if not deleted:
        raise HTTPException(404, "Таблица маппинга не найдена")


# ── Колонки ──────────────────────────────────────────────────────────────────


@router.get("/{table_id}/columns", response_model=list[MappingColumnOut])
async def list_columns(
    _: CurrentUser, table_id: int, project: ValidProject, db: DBSession
):
    table = await svc.get_one(db, project.id, table_id)
    if not table:
        raise HTTPException(404, "Таблица маппинга не найдена")
    return await svc.get_columns(db, table_id)


@router.get("/{table_id}/columns/{column_id}", response_model=MappingColumnOut)
async def get_column(
    _: CurrentUser,
    table_id: int,
    column_id: int,
    project: ValidProject,
    db: DBSession,
):
    # project проверяет принадлежность project_id; table — через get_column
    obj = await svc.get_column(db, table_id, column_id)
    if not obj:
        raise HTTPException(404, "Колонка не найдена")
    return obj


@router.post("/{table_id}/columns", response_model=MappingColumnOut, status_code=201)
async def create_column(
    _: CurrentUser,
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
    _: CurrentUser,
    table_id: int,
    column_id: int,
    payload: MappingColumnCreate,
    project: ValidProject,
    db: DBSession,
) -> MappingColumn | None:
    result = await db.execute(
        select(MappingColumn).where(
            MappingColumn.id == column_id,
            MappingColumn.table_id == table_id,
        )
    )
    obj = result.scalar_one_or_none()
    if not obj:
        return None

    update_data = payload.model_dump(exclude_unset=True)

    # Мёржим текущее состояние с патчем для кросс-полевой валидации
    merged_is_calculated = update_data.get("is_calculated", obj.is_calculated)
    merged_formula = update_data.get("formula", obj.formula)

    if merged_is_calculated and not merged_formula:
        raise HTTPException(
            status_code=422,
            detail=[
                {
                    "loc": ["body", "formula"],
                    "msg": "formula обязательна когда is_calculated=True",
                    "type": "value_error.missing",
                }
            ],
        )

    for key, value in update_data.items():
        setattr(obj, key, value)

    await db.commit()
    await db.refresh(obj)
    return obj


@router.delete("/{table_id}/columns/{column_id}", status_code=204)
async def delete_column(
    _: CurrentUser,
    table_id: int,
    column_id: int,
    project: ValidProject,
    db: DBSession,
):
    deleted = await svc.delete_column(db, table_id, column_id)
    if not deleted:
        raise HTTPException(404, "Колонка не найдена")
