from typing import Optional, Annotated
from fastapi import APIRouter, HTTPException, Query, Path
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.dependencies import DBSession, PaginationDep
from app.schemas.rpi_mapping import (
    RPIMappingCreate, RPIMappingUpdate, RPIMappingOut, RPIStatsOut,
)
from app.services import rpi_mappings as svc
from app.services import projects as project_svc

router = APIRouter(prefix="/projects/{project_id}/rpi-mappings", tags=["RPI Mappings"])


# ── Вспомогательная функция: загрузка проекта по project_id ─────
async def get_project(db: AsyncSession, project_id: int):
    project = await project_svc.get_one(db, project_id)
    if not project:
        raise HTTPException(404, "Проект не найден")
    return project


# ⚠️ /stats до /{rpi_id} — иначе FastAPI примет "stats" как int
@router.get("/stats", response_model=RPIStatsOut)
async def get_stats(db: DBSession, project_id: Annotated[int, Path(...)]):
    project = await get_project(db, project_id)
    return await svc.get_stats(db, project.id)


@router.get("", response_model=list[RPIMappingOut])
@router.get("/", response_model=list[RPIMappingOut])
async def list_rpi_mappings(
    pagination       : PaginationDep,
    db               : DBSession,
    project_id       : Annotated[int, Path(...)],
    status           : Optional[str]  = Query(None, description="approved | in_review | draft"),
    ownership        : Optional[str]  = Query(None),
    measurement_type : Optional[str]  = Query(None, description="dimension | metric"),
    is_calculated    : Optional[bool] = Query(None),
    search           : Optional[str]  = Query(None, description="Поиск по measurement, object_field, ownership"),
):
    project = await get_project(db, project_id)
    return await svc.get_list(
        db, project.id,
        status=status,
        ownership=ownership,
        measurement_type=measurement_type,
        is_calculated=is_calculated,
        search=search,
        skip=pagination.skip,
        limit=pagination.limit,
    )


@router.get("/{rpi_id}", response_model=RPIMappingOut)
async def get_rpi_mapping(rpi_id: int, db: DBSession, project_id: Annotated[int, Path(...)]):
    project = await get_project(db, project_id)
    obj = await svc.get_one(db, project.id, rpi_id)
    if not obj:
        raise HTTPException(404, "Запись РПИ не найдена")
    return obj


@router.post("", response_model=RPIMappingOut, status_code=201)
@router.post("/", response_model=RPIMappingOut, status_code=201)
async def create_rpi_mapping(
    payload: RPIMappingCreate, db: DBSession, project_id: Annotated[int, Path(...)]
):
    project = await get_project(db, project_id)
    return await svc.create(db, project.id, payload)


@router.patch("/{rpi_id}", response_model=RPIMappingOut)
async def update_rpi_mapping(
    rpi_id: int, payload: RPIMappingUpdate, db: DBSession, project_id: Annotated[int, Path(...)]
):
    project = await get_project(db, project_id)
    obj = await svc.update(db, project.id, rpi_id, payload)
    if not obj:
        raise HTTPException(404, "Запись РПИ не найдена")
    return obj


@router.delete("/{rpi_id}", status_code=204)
async def delete_rpi_mapping(rpi_id: int, db: DBSession, project_id: Annotated[int, Path(...)]):
    project = await get_project(db, project_id)
    deleted = await svc.delete(db, project.id, rpi_id)
    if not deleted:
        raise HTTPException(404, "Запись РПИ не найдена")