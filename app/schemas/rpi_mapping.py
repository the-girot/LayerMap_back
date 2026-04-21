from pydantic import BaseModel, model_validator
from datetime import date, datetime
from typing import Optional
from app.models.rpi_mapping import RPIStatus, MeasurementType, ColumnType

# ── MappingColumn ─────────────────────────────────────────────
class MappingColumnBase(BaseModel):
    name          : str
    type          : ColumnType
    data_type     : str
    description   : Optional[str] = None
    is_calculated : bool = False
    formula       : Optional[str] = None

    @model_validator(mode="after")
    def check_formula(self):
        if self.is_calculated and not self.formula:
            raise ValueError("formula обязательна для расчётных колонок")
        return self

class MappingColumnCreate(MappingColumnBase):
    pass

class MappingColumnUpdate(MappingColumnBase):
    name          : Optional[str] = None
    type          : Optional[ColumnType] = None
    data_type     : Optional[str] = None

class MappingColumnOut(MappingColumnBase):
    id               : int
    mapping_table_id : int
    created_at       : datetime

    model_config = {"from_attributes": True}


# ── RPIMapping ────────────────────────────────────────────────
class RPIMappingBase(BaseModel):
    ownership               : Optional[str] = None
    status                  : RPIStatus = RPIStatus.draft
    block                   : Optional[str] = None
    measurement_type        : MeasurementType
    is_calculated           : bool = False
    formula                 : Optional[str] = None
    measurement             : str
    measurement_description : Optional[str] = None
    source_report           : Optional[str] = None
    object_field            : str
    source_column_id        : Optional[int] = None
    date_added              : Optional[date] = None
    date_removed            : Optional[date] = None
    comment                 : Optional[str] = None
    verification_file       : Optional[str] = None

    @model_validator(mode="after")
    def formula_required_if_calculated(self):
        if self.is_calculated and not self.formula:
            raise ValueError("formula обязательна если is_calculated=True")
        return self

class RPIMappingCreate(RPIMappingBase):
    pass

class RPIMappingUpdate(RPIMappingBase):
    measurement  : Optional[str] = None
    object_field : Optional[str] = None
    measurement_type : Optional[MeasurementType] = None

class RPIMappingOut(RPIMappingBase):
    id         : int
    number     : Optional[int]
    project_id : int
    created_at : datetime
    updated_at : datetime

    model_config = {"from_attributes": True}


# ── Stats ─────────────────────────────────────────────────────
class RPIStatsOut(BaseModel):
    total     : int
    approved  : int
    in_review : int
    draft     : int