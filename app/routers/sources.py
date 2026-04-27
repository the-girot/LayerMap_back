# app/routers/sources.py
from fastapi import APIRouter, HTTPException

from app.core.auth import CurrentUser
from app.core.dependencies import ValidProject
from app.database import DBSession
from app.schemas.source import SourceCreate, SourceDetailOut, SourceOut, SourceUpdate
from app.services import sources as svc

router = APIRouter(prefix="/projects/{project_id}/sources", tags=["Sources"])


@router.get("", response_model=list[SourceOut])
@router.get("/", response_model=list[SourceOut])
async def list_sources(
    _: CurrentUser,
    project: ValidProject,
    db: DBSession,
):
    return await svc.get_list(db, project.id)


@router.get("/{source_id}", response_model=SourceDetailOut)
async def get_source(
    db: DBSession, _: CurrentUser, source_id: int, project: ValidProject
):
    obj = await svc.get_one(db, project.id, source_id)
    if not obj:
        raise HTTPException(404, "Источник не найден")
    return obj


@router.post("", response_model=SourceOut, status_code=201)
async def create_source(
    _: CurrentUser, payload: SourceCreate, project: ValidProject, db: DBSession
):
    return await svc.create(db, project.id, payload)


@router.patch("/{source_id}", response_model=SourceOut)
async def update_source(
    _: CurrentUser,
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
async def delete_source(
    _: CurrentUser, source_id: int, project: ValidProject, db: DBSession
):
    deleted = await svc.delete(db, project.id, source_id)
    if not deleted:
        raise HTTPException(404, "Источник не найден")
