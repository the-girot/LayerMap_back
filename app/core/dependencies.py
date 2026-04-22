from dataclasses import dataclass
from typing import Annotated

from fastapi import Depends, HTTPException, Path, Query

from app.database import DBSession
from app.models.project import Project
from app.services import projects as project_svc


async def get_project_or_404(
    db: DBSession,
    project_id: int = Path(...),
) -> Project:
    project = await project_svc.get_one(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Проект не найден")
    return project


ValidProject = Annotated[Project, Depends(get_project_or_404)]


@dataclass
class Pagination:
    skip: int = Query(default=0, ge=0)
    limit: int = Query(default=20, ge=1, le=100)


PaginationDep = Annotated[Pagination, Depends(Pagination)]
