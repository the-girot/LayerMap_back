from pydantic import BaseModel, model_validator
from typing import Optional
from datetime import datetime
from app.models.rpi_mapping import ColumnType


# ── MappingColumn ─────────────────────────────────────────────
class MappingColumnBase(BaseModel):
    name          : str
    type          : ColumnType     = ColumnType.dimension
    data_type     : str
    description   : Optional[str] = None
    is_calculated : bool           = False
    formula       : Optional[str]  = None

    @model_validator(mode="after")
    def check_formula(self):
        if self.is_calculated and not self.formula:
            raise ValueError("formula обязательна для расчётных колонок")
        if not self.is_calculated and self.formula:
            self.formula = None
        return self


class MappingColumnCreate(MappingColumnBase):
    pass


class MappingColumnUpdate(BaseModel):
    name          : Optional[str]        = None
    type          : Optional[ColumnType] = None
    data_type     : Optional[str]        = None
    description   : Optional[str]        = None
    is_calculated : Optional[bool]       = None
    formula       : Optional[str]        = None


class MappingColumnOut(MappingColumnBase):
    id               : int
    mapping_table_id : int
    created_at       : datetime

    model_config = {"from_attributes": True}


# ── MappingTable ──────────────────────────────────────────────
class MappingTableBase(BaseModel):
    name        : str
    description : Optional[str] = None
    source_id   : Optional[int] = None


class MappingTableCreate(MappingTableBase):
    pass


class MappingTableUpdate(BaseModel):
    name        : Optional[str] = None
    description : Optional[str] = None
    source_id   : Optional[int] = None


class MappingTableOut(MappingTableBase):
    id         : int
    project_id : int
    created_at : datetime
    updated_at : datetime
    columns    : list[MappingColumnOut] = []

    model_config = {"from_attributes": True}