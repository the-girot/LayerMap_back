"""
Pydantic-схемы для DWH-моделей: DWHTable, DWHColumn, LayerMapping + lineage.

Следуют тому же шаблону, что и существующие схемы в проекте:
  - *Create — создание сущности
  - *Update — частичное обновление (PATCH)
  - *Out — полное представление для ответа API
  - LineageOut — агрегированный ответ для /lineage
"""

from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from app.models.dwh import DWHLayer


# ──────────────────────────────────────────────────────────────────────
# DWHColumn
# ──────────────────────────────────────────────────────────────────────


class DWHColumnBase(BaseModel):
    """Базовые поля колонки."""

    name: str = Field(..., max_length=255, min_length=1)
    data_type: str = Field(..., max_length=64)
    description: str | None = None
    is_calculated: bool = False
    formula: str | None = None


class DWHColumnCreate(DWHColumnBase):
    """Создание колонки."""

    @field_validator("formula")
    @classmethod
    def formula_required_if_calculated(cls, v, info):
        is_calc = info.data.get("is_calculated")
        if is_calc and not v:
            raise ValueError("formula обязательна если is_calculated=True")
        return v


class DWHColumnUpdate(BaseModel):
    """Частичное обновление колонки (PATCH)."""

    name: str | None = Field(default=None, max_length=255, min_length=1)
    data_type: str | None = Field(default=None, max_length=64)
    description: str | None = None
    is_calculated: bool | None = None
    formula: str | None = None


class DWHColumnOut(DWHColumnBase):
    """Полное представление колонки."""

    id: int
    dwh_table_id: int
    created_at: datetime

    model_config = {"from_attributes": True}


# ──────────────────────────────────────────────────────────────────────
# DWHTable
# ──────────────────────────────────────────────────────────────────────


class DWHTableBase(BaseModel):
    """Базовые поля DWH-таблицы."""

    name: str = Field(..., max_length=255, min_length=1)
    layer: DWHLayer
    description: str | None = None


class DWHTableCreate(DWHTableBase):
    """Создание DWH-таблицы."""
    pass


class DWHTableUpdate(BaseModel):
    """Частичное обновление DWH-таблицы (PATCH)."""

    name: str | None = Field(default=None, max_length=255, min_length=1)
    description: str | None = None


class DWHTableOut(DWHTableBase):
    """Полное представление DWH-таблицы с колонками."""

    id: int
    project_id: int
    created_at: datetime
    updated_at: datetime
    columns: list[DWHColumnOut] = []

    model_config = {"from_attributes": True}


class DWHTableSummaryOut(BaseModel):
    """Краткое представление DWH-таблицы (без колонок)."""

    id: int
    project_id: int
    layer: DWHLayer
    name: str
    description: str | None

    model_config = {"from_attributes": True}


# ──────────────────────────────────────────────────────────────────────
# LayerMappingSource
# ──────────────────────────────────────────────────────────────────────


class LayerMappingSourceOut(BaseModel):
    """Исходная таблица в составе маппинга."""

    id: int
    mapping_id: int
    source_table_id: int

    model_config = {"from_attributes": True}


# ──────────────────────────────────────────────────────────────────────
# LayerMapping
# ──────────────────────────────────────────────────────────────────────


class LayerMappingBase(BaseModel):
    """Базовые поля маппинга."""

    transformation: str | None = None
    algorithm: str | None = None


class LayerMappingCreate(LayerMappingBase):
    """Создание маппинга.

    targetTableId — целевая DWH-таблица.
    sourceTableIds — список ID исходных DWH-таблиц (непустой).
    """

    target_table_id: int = Field(..., alias="targetTableId")
    source_table_ids: list[int] = Field(
        ..., min_length=1, alias="sourceTableIds"
    )

    @field_validator("source_table_ids")
    @classmethod
    def validate_source_table_ids(cls, v):
        if not v or len(v) == 0:
            raise ValueError("source_table_ids не должен быть пустым")
        if len(v) != len(set(v)):
            raise ValueError("source_table_ids содержит дубликаты")
        return v

    model_config = {"populate_by_name": True}


class LayerMappingUpdate(BaseModel):
    """Частичное обновление маппинга (PATCH).

    Все поля необязательны. transformation и algorithm можно обновлять
    по отдельности.
    """

    transformation: str | None = None
    algorithm: str | None = None


class LayerMappingOut(LayerMappingBase):
    """Полное представление маппинга с раскрытыми данными."""

    id: int
    project_id: int
    target_table_id: int
    created_at: datetime
    updated_at: datetime

    # раскрытые связи
    target_table: DWHTableSummaryOut | None = None
    sources: list[LayerMappingSourceOut] = []
    source_tables: list[DWHTableSummaryOut] = []

    model_config = {"from_attributes": True}


# ──────────────────────────────────────────────────────────────────────
# Lineage — агрегированный ответ для /projects/{id}/lineage
# ──────────────────────────────────────────────────────────────────────


class LineageTableNode(BaseModel):
    """Узел графа lineage: одна DWH-таблица."""

    id: int
    layer: DWHLayer
    name: str
    description: str | None
    columns: list[DWHColumnOut] = []


class LineageMappingEdge(BaseModel):
    """Ребро графа lineage: маппинг с исходными таблицами."""

    id: int
    target_table_id: int
    source_table_ids: list[int] = []
    transformation: str | None
    algorithm: str | None


class LineageOut(BaseModel):
    """Агрегированный ответ для загрузки страницы lineage.

    Содержит все таблицы проекта, их колонки и список маппингов.
    Frontend строит граф, сопоставляя target_table_id с source_table_ids.
    """

    tables: list[LineageTableNode] = []
    mappings: list[LineageMappingEdge] = []
