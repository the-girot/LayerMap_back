"""
Модели DWH-слоёв: DWHLayer, DWHTable, DWHColumn, LayerMapping, LayerMappingSource.

Domain:
  - DWHLayer (enum): STG, ODS, DDS, DM — фиксированные типы слоёв хранилища.
  - DWHTable: таблица в определённом слое DWH.
  - DWHColumn: колонка DWH-таблицы.
  - LayerMapping: правило переноса данных между таблицами (lineage).
  - LayerMappingSource: одна исходная таблица в составе маппинга.
"""

import enum
from datetime import UTC, datetime

from sqlalchemy import (
    DateTime,
    Enum,
    ForeignKey,
    Index,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


# ──────────────────────────────────────────────────────────────────────
# DWHLayer — фиксированный enum слоёв хранилища
# ──────────────────────────────────────────────────────────────────────


class DWHLayer(str, enum.Enum):
    """Слои корпоративного хранилища данных."""

    STG = "STG"  # Staging — сырые данные из источников
    ODS = "ODS"  # Operational Data Store — очищенные операционные данные
    DDS = "DDS"  # Detail Data Store — детальные данные в dimensional модели
    DM = "DM"  # Data Mart — витрины данных для отчётов


# ──────────────────────────────────────────────────────────────────────
# DWHTable — таблица в DWH
# ──────────────────────────────────────────────────────────────────────


class DWHTable(Base):
    __tablename__ = "dwh_tables"

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    layer: Mapped[DWHLayer] = mapped_column(
        Enum(DWHLayer, name="dwhlayer"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=lambda: datetime.now(UTC),
    )

    # relationships
    project: Mapped["Project"] = relationship(back_populates="dwh_tables")  # type: ignore[name-defined]
    columns: Mapped[list["DWHColumn"]] = relationship(
        back_populates="table",
        cascade="all, delete-orphan",
    )

    # маппинг, в котором эта таблица является ЦЕЛЬЮ (один-к-одному)
    target_mapping: Mapped["LayerMapping | None"] = relationship(
        back_populates="target_table",
        uselist=False,
        cascade="all, delete-orphan",
    )

    # маппинги, в которых эта таблица является ИСТОЧНИКОМ
    source_links: Mapped[list["LayerMappingSource"]] = relationship(
        back_populates="source_table",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        UniqueConstraint(
            "project_id",
            "layer",
            "name",
            name="uq_dwh_tables_project_layer_name",
        ),
        Index("ix_dwh_tables_layer", "layer"),
        Index("ix_dwh_tables_project_layer", "project_id", "layer"),
    )


# ──────────────────────────────────────────────────────────────────────
# DWHColumn — колонка DWH-таблицы
# ──────────────────────────────────────────────────────────────────────


class DWHColumn(Base):
    __tablename__ = "dwh_columns"

    id: Mapped[int] = mapped_column(primary_key=True)
    dwh_table_id: Mapped[int] = mapped_column(
        ForeignKey("dwh_tables.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    data_type: Mapped[str] = mapped_column(String(64), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_calculated: Mapped[bool] = mapped_column(default=False)
    formula: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    table: Mapped["DWHTable"] = relationship(back_populates="columns")


# ──────────────────────────────────────────────────────────────────────
# LayerMapping — маппинг (правило переноса) между таблицами
# ──────────────────────────────────────────────────────────────────────


class LayerMapping(Base):
    __tablename__ = "layer_mappings"

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    target_table_id: Mapped[int] = mapped_column(
        ForeignKey("dwh_tables.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,  # одна таблица может быть целью только одного маппинга
    )
    transformation: Mapped[str | None] = mapped_column(Text, nullable=True)
    algorithm: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=lambda: datetime.now(UTC),
    )

    # relationships
    project: Mapped["Project"] = relationship(back_populates="layer_mappings")  # type: ignore[name-defined]
    target_table: Mapped["DWHTable"] = relationship(
        back_populates="target_mapping",
        foreign_keys=[target_table_id],
    )
    sources: Mapped[list["LayerMappingSource"]] = relationship(
        back_populates="mapping",
        cascade="all, delete-orphan",
    )


# ──────────────────────────────────────────────────────────────────────
# LayerMappingSource — одна исходная таблица в составе маппинга
# ──────────────────────────────────────────────────────────────────────


class LayerMappingSource(Base):
    __tablename__ = "layer_mapping_sources"

    id: Mapped[int] = mapped_column(primary_key=True)
    mapping_id: Mapped[int] = mapped_column(
        ForeignKey("layer_mappings.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    source_table_id: Mapped[int] = mapped_column(
        ForeignKey("dwh_tables.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    mapping: Mapped["LayerMapping"] = relationship(back_populates="sources")
    source_table: Mapped["DWHTable"] = relationship(
        back_populates="source_links",
        foreign_keys=[source_table_id],
    )

    __table_args__ = (
        UniqueConstraint(
            "mapping_id",
            "source_table_id",
            name="uq_mapping_source",
        ),
    )
