
# app/schemas/source.py

from datetime import datetime

from pydantic import BaseModel

from app.models.source import SourceType
from app.schemas.mapping_table import MappingTableOut  # или Summary-версию


class SourceDetailOut(BaseModel):
    id: int
    project_id: int
    name: str
    description: str | None = None
    type: SourceType
    row_count: int
    last_updated: datetime | None = None
    created_at: datetime

    # связанная таблица, если есть
    mapping_table: MappingTableOut | None = None

    model_config = {"from_attributes": True}


class SourceBase(BaseModel):
    name: str
    description: str | None = None
    type: SourceType = SourceType.DB
    row_count: int = 0
    mapping_table_id: int | None = None  # ← это остаётся (FK в Source)
    last_updated: datetime | None = None


class SourceCreate(SourceBase):
    type: SourceType


class SourceUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    type: SourceType | None = None
    row_count: int | None = None
    mapping_table_id: int | None = None
    last_updated: datetime | None = None


class SourceOut(SourceBase):
    id: int
    project_id: int
    created_at: datetime

    model_config = {"from_attributes": True}
