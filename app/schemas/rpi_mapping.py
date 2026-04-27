from datetime import date, datetime

from pydantic import BaseModel, model_validator

from app.models.rpi_mapping import MeasurementType, RPIStatus
from app.models.source_table import ColumnType
from app.schemas.source_table import SourceColumnOut


# ── RPIMapping ────────────────────────────────────────────────
class RPIMappingBase(BaseModel):
    ownership: str | None = None
    status: RPIStatus = RPIStatus.draft
    block: str | None = None
    measurement_type: MeasurementType
    is_calculated: bool = False
    formula: str | None = None
    measurement: str
    measurement_description: str | None = None
    source_report: str | None = None
    object_field: str
    source_column_id: int | None = None
    date_added: date | None = None
    date_removed: date | None = None
    comment: str | None = None
    verification_file: str | None = None

    @model_validator(mode="after")
    def formula_required_if_calculated(self):
        if self.is_calculated and not self.formula:
            raise ValueError("formula обязательна если is_calculated=True")
        return self


class RPIMappingCreate(RPIMappingBase):
    pass


class RPIMappingUpdate(RPIMappingBase):
    measurement: str | None = None
    object_field: str | None = None
    measurement_type: MeasurementType | None = None


class RPIMappingOut(RPIMappingBase):
    id: int
    number: int | None
    project_id: int
    created_at: datetime
    updated_at: datetime

    # вложенная колонка источника
    source_column: SourceColumnOut | None = None

    model_config = {"from_attributes": True}


# ── Stats ─────────────────────────────────────────────────────
class RPIStatsOut(BaseModel):
    total: int
    approved: int
    in_review: int
    draft: int
