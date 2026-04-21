from typing import Annotated
from fastapi import Depends, HTTPException, Header, Query, Path
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models.project import Project
from app.services import projects as project_svc
from contextlib import asynccontextmanager
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from dataclasses import dataclass


# ── DB сессия ─────────────────────────────────────────────────
DBSession = Annotated[AsyncSession, Depends(get_db)]


# ── Получение проекта по project_id из пути ───────────────────
async def get_project_or_404(
    db: Annotated[AsyncSession, Depends(get_db)],
    project_id: int = Path(...),
) -> Project:
    project = await project_svc.get_one(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Проект не найден")
    return project

ValidProject = Annotated[Project, Depends(get_project_or_404)]



# ── Пагинация ─────────────────────────────────────────────────
@dataclass
class Pagination:
    skip  : int = Query(default=0,  ge=0)
    limit : int = Query(default=20, ge=1, le=100)

PaginationDep = Annotated[Pagination, Depends(Pagination)]

