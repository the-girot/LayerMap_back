import enum
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class ColumnType(enum.StrEnum):
    dimension = "dimension"
    metric = "metric"


class SourceColumn(Base):
    __tablename__ = "source_columns"

    id: Mapped[int] = mapped_column(primary_key=True)
    source_table_id: Mapped[int] = mapped_column(
        ForeignKey("source_tables.id", ondelete="CASCADE")
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

    table: Mapped["SourceTable"] = relationship(back_populates="columns")
    rpi_mappings: Mapped[list["RPIMapping"]] = relationship(
        back_populates="source_column"
    )


class SourceTable(Base):
    __tablename__ = "source_tables"

    id: Mapped[int] = mapped_column(primary_key=True)
    source_id: Mapped[int] = mapped_column(
        ForeignKey("sources.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    source: Mapped["Source"] = relationship(back_populates="tables")
    columns: Mapped[list["SourceColumn"]] = relationship(
        back_populates="table", cascade="all, delete-orphan"
    )
