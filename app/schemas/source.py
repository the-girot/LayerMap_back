from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from app.models.source import SourceType


class SourceBase(BaseModel):
    name             : str
    description      : Optional[str]  = None
    type             : SourceType     = SourceType.DB
    row_count        : int            = 0
    mapping_table_id : Optional[int]  = None
    last_updated     : Optional[datetime] = None


class SourceCreate(SourceBase):
    pass


class SourceUpdate(BaseModel):
    name             : Optional[str]      = None
    description      : Optional[str]      = None
    type             : Optional[SourceType] = None
    row_count        : Optional[int]      = None
    mapping_table_id : Optional[int]      = None
    last_updated     : Optional[datetime] = None


class SourceOut(SourceBase):
    id         : int
    project_id : int
    created_at : datetime

    model_config = {"from_attributes": True}