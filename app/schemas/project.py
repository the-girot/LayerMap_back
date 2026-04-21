from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from app.models.project import ProjectStatus


class ProjectBase(BaseModel):
    name        : str
    description : Optional[str] = None
    status      : ProjectStatus = ProjectStatus.draft


class ProjectCreate(ProjectBase):
    pass


class ProjectUpdate(BaseModel):
    name        : Optional[str]           = None
    description : Optional[str]           = None
    status      : Optional[ProjectStatus] = None


class ProjectOut(ProjectBase):
    id         : int
    created_at : datetime
    updated_at : datetime

    model_config = {"from_attributes": True}