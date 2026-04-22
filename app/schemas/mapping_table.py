from datetime import datetime

from pydantic import BaseModel, ConfigDict, model_validator

from app.models.mapping_table import ColumnType


# ── MappingColumn ─────────────────────────────────────────────
class MappingColumnBase(BaseModel):
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


class MappingColumnCreate(MappingColumnBase):
    pass


class MappingColumnUpdate(BaseModel):
    name: str | None = None
    type: ColumnType | None = None
    data_type: str | None = None
    description: str | None = None
    is_calculated: bool | None = None
    formula: str | None = None


class MappingColumnOut(MappingColumnBase):
    id: int
    mapping_table_id: int
    created_at: datetime

    model_config = {"from_attributes": True}


# ── MappingTable ──────────────────────────────────────────────
class MappingTableBase(BaseModel):
    name: str
    description: str | None = None


class MappingTableCreate(MappingTableBase):
    source_id: int | None = None


class MappingTableUpdate(BaseModel):
    name: str | None = None
    description: str | None = None


class MappingTableOut(MappingTableBase):
    id: int
    project_id: int
    source_id: int | None = None  # вычисляется через Sources
    created_at: datetime
    updated_at: datetime
    columns: list["MappingColumnOut"] = []

    model_config = ConfigDict(from_attributes=True)
