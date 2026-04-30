"""
FastAPI-роутеры для DWH-модуля.

URL-структура (все эндпоинты project-scoped):
  - /projects/{project_id}/dwh-tables          — CRUD таблиц
  - /projects/{project_id}/dwh-tables/{table_id}/columns  — CRUD колонок
  - /projects/{project_id}/layer-mappings       — CRUD маппингов
  - /projects/{project_id}/lineage              — lineage-граф

Авторизация: все эндпоинты доступны аутентифицированным участникам проекта.
"""

from fastapi import APIRouter, HTTPException

from app.core.auth import CurrentUser
from app.core.dependencies import ValidProject
from app.database import DBSession
from app.schemas.dwh import (
    DWHColumnCreate,
    DWHColumnOut,
    DWHColumnUpdate,
    DWHTableCreate,
    DWHTableOut,
    DWHTableUpdate,
    LayerMappingCreate,
    LayerMappingOut,
    LayerMappingUpdate,
    LineageOut,
)
from app.services import dwh as svc

router = APIRouter(prefix="/projects/{project_id}", tags=["DWH"])


# ══════════════════════════════════════════════════════════════════════
# DWHTable CRUD
# ══════════════════════════════════════════════════════════════════════


@router.get("/dwh-tables", response_model=list[DWHTableOut])
@router.get("/dwh-tables/", response_model=list[DWHTableOut])
async def list_dwh_tables(
    _: CurrentUser,
    project: ValidProject,
    db: DBSession,
):
    """Получить все DWH-таблицы проекта."""
    return await svc.get_tables(db, project.id)


@router.get("/dwh-tables/{table_id}", response_model=DWHTableOut)
async def get_dwh_table(
    _: CurrentUser,
    table_id: int,
    project: ValidProject,
    db: DBSession,
):
    """Получить одну DWH-таблицу с колонками."""
    obj = await svc.get_table(db, project.id, table_id)
    if not obj:
        raise HTTPException(404, "DWH-таблица не найдена")
    return obj


@router.post("/dwh-tables", response_model=DWHTableOut, status_code=201)
@router.post("/dwh-tables/", response_model=DWHTableOut, status_code=201)
async def create_dwh_table(
    _: CurrentUser,
    payload: DWHTableCreate,
    project: ValidProject,
    db: DBSession,
):
    """Создать новую DWH-таблицу."""
    return await svc.create_table(db, project.id, payload)


@router.patch("/dwh-tables/{table_id}", response_model=DWHTableOut)
async def update_dwh_table(
    _: CurrentUser,
    table_id: int,
    payload: DWHTableUpdate,
    project: ValidProject,
    db: DBSession,
):
    """Обновить DWH-таблицу (PATCH, частичное обновление)."""
    obj = await svc.update_table(db, project.id, table_id, payload)
    if not obj:
        raise HTTPException(404, "DWH-таблица не найдена")
    return obj


@router.delete("/dwh-tables/{table_id}", status_code=204)
async def delete_dwh_table(
    _: CurrentUser,
    table_id: int,
    project: ValidProject,
    db: DBSession,
):
    """Удалить DWH-таблицу (каскадно удаляет колонки и маппинги)."""
    deleted = await svc.delete_table(db, project.id, table_id)
    if not deleted:
        raise HTTPException(404, "DWH-таблица не найдена")


# ══════════════════════════════════════════════════════════════════════
# DWHColumn CRUD
# ══════════════════════════════════════════════════════════════════════


@router.get(
    "/dwh-tables/{table_id}/columns",
    response_model=list[DWHColumnOut],
)
async def list_dwh_columns(
    _: CurrentUser,
    table_id: int,
    project: ValidProject,
    db: DBSession,
):
    """Получить колонки DWH-таблицы."""
    table = await svc.get_table(db, project.id, table_id)
    if not table:
        raise HTTPException(404, "DWH-таблица не найдена")
    return await svc.get_columns(db, table_id)


@router.get(
    "/dwh-tables/{table_id}/columns/{column_id}",
    response_model=DWHColumnOut,
)
async def get_dwh_column(
    _: CurrentUser,
    table_id: int,
    column_id: int,
    project: ValidProject,
    db: DBSession,
):
    """Получить одну колонку DWH-таблицы."""
    obj = await svc.get_column(db, table_id, column_id)
    if not obj:
        raise HTTPException(404, "Колонка не найдена")
    return obj


@router.post(
    "/dwh-tables/{table_id}/columns",
    response_model=DWHColumnOut,
    status_code=201,
)
async def create_dwh_column(
    _: CurrentUser,
    table_id: int,
    payload: DWHColumnCreate,
    project: ValidProject,
    db: DBSession,
):
    """Создать колонку в DWH-таблице."""
    table = await svc.get_table(db, project.id, table_id)
    if not table:
        raise HTTPException(404, "DWH-таблица не найдена")
    return await svc.create_column(db, table_id, payload)


@router.patch(
    "/dwh-tables/{table_id}/columns/{column_id}",
    response_model=DWHColumnOut,
)
async def update_dwh_column(
    _: CurrentUser,
    table_id: int,
    column_id: int,
    payload: DWHColumnUpdate,
    project: ValidProject,
    db: DBSession,
):
    """Обновить колонку (PATCH, частичное обновление)."""
    obj = await svc.update_column(db, table_id, column_id, payload)
    if not obj:
        raise HTTPException(404, "Колонка не найдена")
    return obj


@router.delete(
    "/dwh-tables/{table_id}/columns/{column_id}",
    status_code=204,
)
async def delete_dwh_column(
    _: CurrentUser,
    table_id: int,
    column_id: int,
    project: ValidProject,
    db: DBSession,
):
    """Удалить колонку."""
    deleted = await svc.delete_column(db, table_id, column_id)
    if not deleted:
        raise HTTPException(404, "Колонка не найдена")


# ══════════════════════════════════════════════════════════════════════
# LayerMapping CRUD
# ══════════════════════════════════════════════════════════════════════


@router.get("/layer-mappings", response_model=list[LayerMappingOut])
@router.get("/layer-mappings/", response_model=list[LayerMappingOut])
async def list_layer_mappings(
    _: CurrentUser,
    project: ValidProject,
    db: DBSession,
):
    """Получить все маппинги слоёв проекта."""
    return await svc.get_mappings(db, project.id)


@router.get("/layer-mappings/{mapping_id}", response_model=LayerMappingOut)
async def get_layer_mapping(
    _: CurrentUser,
    mapping_id: int,
    project: ValidProject,
    db: DBSession,
):
    """Получить один маппинг с источниками."""
    obj = await svc.get_mapping(db, project.id, mapping_id)
    if not obj:
        raise HTTPException(404, "Маппинг не найден")
    return obj


@router.post(
    "/layer-mappings",
    response_model=LayerMappingOut,
    status_code=201,
)
@router.post(
    "/layer-mappings/",
    response_model=LayerMappingOut,
    status_code=201,
)
async def create_layer_mapping(
    _: CurrentUser,
    payload: LayerMappingCreate,
    project: ValidProject,
    db: DBSession,
):
    """Создать маппинг между таблицами слоёв.

    Тело запроса:
      targetTableId (int): целевая DWH-таблица.
      sourceTableIds (list[int]): список ID исходных таблиц (непустой).
      transformation (str, опционально): описание трансформации.
      algorithm (str, опционально): описание алгоритма.

    Бизнес-правила:
      - ODS собирается только из одной STG.
      - DDS — из одной или нескольких ODS (или STG).
      - DM — из одной или нескольких DDS/ODS.
      - Все таблицы должны быть из одного проекта.
      - Запрещены циклы в графе lineage.
    """
    return await svc.create_mapping(db, project.id, payload)


@router.patch("/layer-mappings/{mapping_id}", response_model=LayerMappingOut)
async def update_layer_mapping(
    _: CurrentUser,
    mapping_id: int,
    payload: LayerMappingUpdate,
    project: ValidProject,
    db: DBSession,
):
    """Обновить маппинг (PATCH, только transformation и algorithm).

    Для изменения состава источников нужно удалить и создать маппинг заново.
    """
    obj = await svc.update_mapping(db, project.id, mapping_id, payload)
    if not obj:
        raise HTTPException(404, "Маппинг не найден")
    return obj


@router.delete("/layer-mappings/{mapping_id}", status_code=204)
async def delete_layer_mapping(
    _: CurrentUser,
    mapping_id: int,
    project: ValidProject,
    db: DBSession,
):
    """Удалить маппинг."""
    deleted = await svc.delete_mapping(db, project.id, mapping_id)
    if not deleted:
        raise HTTPException(404, "Маппинг не найден")


# ══════════════════════════════════════════════════════════════════════
# Lineage
# ══════════════════════════════════════════════════════════════════════


@router.get("/lineage", response_model=LineageOut)
async def get_project_lineage(
    _: CurrentUser,
    project: ValidProject,
    db: DBSession,
):
    """Получить полный граф lineage проекта.

    Возвращает все DWH-таблицы с колонками и все маппинги с target/source.
    Frontend строит граф, сопоставляя target_table_id с source_table_ids.
    """
    return await svc.get_lineage(db, project.id)
