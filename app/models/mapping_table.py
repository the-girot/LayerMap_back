import enum
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class ColumnType(enum.StrEnum):
    dimension = "dimension"
    metric = "metric"


class MappingColumn(Base):
    __tablename__ = "mapping_columns"

    id: Mapped[int] = mapped_column(primary_key=True)
    mapping_table_id: Mapped[int] = mapped_column(
        ForeignKey("mapping_tables.id", ondelete="CASCADE")
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    type: Mapped[ColumnType] = mapped_column(
        Enum(ColumnType), default=ColumnType.dimension
    )
    data_type: Mapped[str] = mapped_column(String(64), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    is_calculated: Mapped[bool] = mapped_column(Boolean, server_default="false")
    formula: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    mapping_table: Mapped["MappingTable"] = relationship(back_populates="columns")
    rpi_mappings: Mapped[list["RPIMapping"]] = relationship(
        back_populates="source_column"
    )

class MappingTable(Base):
    __tablename__ = "mapping_tables"
    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"))
    # ❌ Убрать: source_id: Mapped[int | None] = mapped_column(ForeignKey("sources.id", ...))
    name: Mapped[str]
    description: Mapped[str | None]
    created_at: Mapped[datetime] = mapped_column(default=func.now())
    updated_at: Mapped[datetime] = mapped_column(default=func.now(), onupdate=func.now())

    project: Mapped["Project"] = relationship(back_populates="mapping_tables")
    columns: Mapped[list["MappingColumn"]] = relationship(back_populates="mapping_table", cascade="all, delete-orphan")

    # One-to-many: один MappingTable → много Sources
    sources: Mapped[list["Source"]] = relationship(
        "Source",
        back_populates="mapping_table",
        foreign_keys="[Source.mapping_table_id]",
    )
