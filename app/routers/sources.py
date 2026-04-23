# app/routers/sources.py
from fastapi import APIRouter, HTTPException

from app.core.auth import CurrentUser
from app.core.dependencies import ValidProject
from app.database import DBSession
from app.schemas.mapping_table import MappingTableCreate, MappingTableOut
from app.schemas.source import SourceCreate, SourceDetailOut, SourceOut, SourceUpdate
from app.services import mapping_tables as mt_svc
from app.services import sources as svc

router = APIRouter(prefix="/projects/{project_id}/sources", tags=["Sources"])


@router.get("", response_model=list[SourceOut])
@router.get("/", response_model=list[SourceOut])
async def list_sources(
    _: CurrentUser,  # ← должно быть здесь
    project: ValidProject,
    db: DBSession,
):
    return await svc.get_list(db, project.id)


@router.get("/{source_id}", response_model=SourceDetailOut)
async def get_source(source_id: int, project: ValidProject, db: DBSession):
    obj = await svc.get_one(db, project.id, source_id)
    if not obj:
        raise HTTPException(404, "Источник не найден")
    return obj


@router.post("", response_model=SourceOut, status_code=201)
@router.post("/", response_model=SourceOut, status_code=201)
async def create_source(payload: SourceCreate, project: ValidProject, db: DBSession):
    return await svc.create(db, project.id, payload)


@router.patch("/{source_id}", response_model=SourceOut)
async def update_source(
    source_id: int,
    payload: SourceUpdate,
    project: ValidProject,
    db: DBSession,
):
    obj = await svc.update(db, project.id, source_id, payload)
    if not obj:
        raise HTTPException(404, "Источник не найден")
    return obj


@router.delete("/{source_id}", status_code=204)
async def delete_source(source_id: int, project: ValidProject, db: DBSession):
    deleted = await svc.delete(db, project.id, source_id)
    if not deleted:
        raise HTTPException(404, "Источник не найден")


@router.get("/{source_id}/mapping-tables", response_model=list[MappingTableOut])
async def list_mapping_tables_by_source(
    source_id: int, project: ValidProject, db: DBSession
):
    src = await svc.get_one(db, project.id, source_id)
    if not src:
        raise HTTPException(404, "Источник не найден")
    return await mt_svc.get_by_source(db, project.id, source_id)


@router.post(
    "/{source_id}/mapping-tables",
    response_model=MappingTableOut,
    status_code=201,
)
async def create_mapping_table_for_source(
    source_id: int,
    payload: MappingTableCreate,
    project: ValidProject,
    db: DBSession,
):
    src = await svc.get_one(db, project.id, source_id)
    if not src:
        raise HTTPException(404, "Источник не найден")
    return await mt_svc.create(db, project.id, payload, source_id=source_id)
