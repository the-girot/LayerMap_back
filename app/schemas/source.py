# app/schemas/source.py

from datetime import datetime

from pydantic import BaseModel, field_validator

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

    @field_validator("mapping_table_id")
    @classmethod
    def mapping_table_id_must_be_positive(cls, v: int | None) -> int | None:
        if v is not None and v <= 0:
            raise ValueError("mapping_table_id должен быть положительным числом")
        return v


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
