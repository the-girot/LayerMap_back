from fastapi import APIRouter, HTTPException, Query

from app.core.auth import CurrentUser
from app.core.dependencies import PaginationDep, ValidProject
from app.database import DBSession
from app.schemas.rpi_mapping import (
    RPIMappingCreate,
    RPIMappingOut,
    RPIMappingUpdate,
    RPIStatsOut,
    RPIStatus,
)
from app.services import rpi_mappings as svc

router = APIRouter(
    prefix="/projects/{project_id}/rpi-mappings",
    tags=["RPI Mappings"],
)


# ⚠️ /stats до /{rpi_id} — иначе FastAPI примет "stats" как int
@router.get("/stats", response_model=RPIStatsOut)
async def get_stats(_: CurrentUser, project: ValidProject, db: DBSession):
    return await svc.get_stats(db, project.id)


@router.get("", response_model=list[RPIMappingOut])
@router.get("/", response_model=list[RPIMappingOut])
async def list_rpi_mappings(
    _: CurrentUser,
    pagination: PaginationDep,
    project: ValidProject,
    db: DBSession,
    status: RPIStatus  | None = Query(None, description="approved | in_review | draft"),
    ownership: str | None = Query(None),
    measurement_type: str | None = Query(None, description="dimension | metric"),
    dimension: str | None = Query(None, description="Фильтр по измерению (частичное совпадение)"),
    is_calculated: bool | None = Query(None),
    search: str | None = Query(
        None, min_length=1, description="Поиск по measurement, dimension, object_field, ownership"
    ),
):
    return await svc.get_list(
        db,
        project.id,
        status=status,
        ownership=ownership,
        measurement_type=measurement_type,
        dimension=dimension,
        is_calculated=is_calculated,
        search=search,
        skip=pagination.skip,
        limit=pagination.limit,
    )


@router.get("/{rpi_id}", response_model=RPIMappingOut)
async def get_rpi_mapping(
    _: CurrentUser, rpi_id: int, project: ValidProject, db: DBSession
):
    obj = await svc.get_one(db, project.id, rpi_id)
    if not obj:
        raise HTTPException(404, "Запись РПИ не найдена")
    return obj


@router.post("", response_model=RPIMappingOut, status_code=201)
@router.post("/", response_model=RPIMappingOut, status_code=201)
async def create_rpi_mapping(
    _: CurrentUser,
    payload: RPIMappingCreate,
    project: ValidProject,
    db: DBSession,
):
    return await svc.create(db, project.id, payload)


@router.patch("/{rpi_id}", response_model=RPIMappingOut)
async def update_rpi_mapping(
    _: CurrentUser,
    rpi_id: int,
    payload: RPIMappingUpdate,
    project: ValidProject,
    db: DBSession,
):
    obj = await svc.update(db, project.id, rpi_id, payload)
    if not obj:
        raise HTTPException(404, "Запись РПИ не найдена")
    return obj


@router.delete("/{rpi_id}", status_code=204)
async def delete_rpi_mapping(
    _: CurrentUser, rpi_id: int, project: ValidProject, db: DBSession
):
    deleted = await svc.delete(db, project.id, rpi_id)
    if not deleted:
        raise HTTPException(404, "Запись РПИ не найдена")
