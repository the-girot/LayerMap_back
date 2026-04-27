from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, model_validator

from app.models.source_table import ColumnType


class DataType(str, Enum):
    string = "string"
    integer = "integer"
    float_ = "float"
    boolean = "boolean"
    date = "date"
    datetime = "datetime"


# ── SourceColumn ─────────────────────────────────────────────
class SourceColumnBase(BaseModel):
    name: str
    type: ColumnType = ColumnType.dimension
    data_type: str
    description: str | None = None
    is_calculated: bool = False
    formula: str | None = None

    @model_validator(mode="after")
    def check_formula(self):
        if self.is_calculated and not self.formula:
            raise ValueError("formula обязательна для расчётных колонок")
        if not self.is_calculated and self.formula:
            self.formula = None
        return self


class SourceColumnCreate(SourceColumnBase):
    data_type: DataType


class SourceColumnUpdate(BaseModel):
    name: str | None = None
    type: ColumnType | None = None
    data_type: str | None = None
    description: str | None = None
    is_calculated: bool | None = None
    formula: str | None = None


class SourceColumnOut(SourceColumnBase):
    id: int
    source_table_id: int
    created_at: datetime

    model_config = {"from_attributes": True}


# ── SourceTable ──────────────────────────────────────────────
class SourceTableBase(BaseModel):
    name: str
    description: str | None = None


class SourceTableCreate(SourceTableBase):
    pass


class SourceTableUpdate(BaseModel):
    name: str | None = None
    description: str | None = None


class SourceTableOut(SourceTableBase):
    id: int
    source_id: int
    created_at: datetime
    updated_at: datetime
    columns: list["SourceColumnOut"] = []

    model_config = ConfigDict(from_attributes=True)
