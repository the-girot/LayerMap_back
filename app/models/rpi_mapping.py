import enum
from datetime import datetime, date
from sqlalchemy import String, Text, Enum, Boolean, Date, ForeignKey, DateTime, Integer, func, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base

class RPIStatus(str, enum.Enum):
    approved  = "approved"
    in_review = "in_review"
    draft     = "draft"

class MeasurementType(str, enum.Enum):
    dimension = "dimension"
    metric    = "metric"

class ColumnType(str, enum.Enum):
    dimension = "dimension"
    metric    = "metric"

class MappingColumn(Base):
    __tablename__ = "mapping_columns"

    id               : Mapped[int]         = mapped_column(primary_key=True)
    mapping_table_id : Mapped[int]         = mapped_column(ForeignKey("mapping_tables.id", ondelete="CASCADE"))
    name             : Mapped[str]         = mapped_column(String(255), nullable=False)
    type             : Mapped[ColumnType]  = mapped_column(Enum(ColumnType), default=ColumnType.dimension)
    data_type        : Mapped[str]         = mapped_column(String(64), nullable=False)
    description      : Mapped[str | None]  = mapped_column(Text)
    is_calculated    : Mapped[bool]        = mapped_column(Boolean, default=False)
    formula          : Mapped[str | None]  = mapped_column(Text)
    created_at       : Mapped[datetime]    = mapped_column(DateTime, server_default=func.now())

    mapping_table : Mapped["MappingTable"] = relationship(back_populates="columns")
    rpi_mappings  : Mapped[list["RPIMapping"]] = relationship(back_populates="source_column")


class RPIMapping(Base):
    __tablename__ = "rpi_mappings"
    __table_args__ = (
        CheckConstraint(
            "(is_calculated = TRUE AND formula IS NOT NULL) OR (is_calculated = FALSE)",
            name="chk_formula"
        ),
    )

    id                      : Mapped[int]             = mapped_column(primary_key=True)
    number                  : Mapped[int | None]      = mapped_column(Integer)
    project_id              : Mapped[int]             = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"))
    source_column_id        : Mapped[int | None]      = mapped_column(ForeignKey("mapping_columns.id", ondelete="SET NULL"))

    ownership               : Mapped[str | None]      = mapped_column(String(128))
    status                  : Mapped[RPIStatus]       = mapped_column(Enum(RPIStatus), default=RPIStatus.draft)
    block                   : Mapped[str | None]      = mapped_column(String(128))
    measurement_type        : Mapped[MeasurementType] = mapped_column(Enum(MeasurementType))
    is_calculated           : Mapped[bool]            = mapped_column(Boolean, default=False)
    formula                 : Mapped[str | None]      = mapped_column(Text)

    measurement             : Mapped[str]             = mapped_column(String(255), nullable=False)
    measurement_description : Mapped[str | None]      = mapped_column(Text)
    source_report           : Mapped[str | None]      = mapped_column(String(255))
    object_field            : Mapped[str]             = mapped_column(String(255), nullable=False)

    date_added              : Mapped[date | None]     = mapped_column(Date)
    date_removed            : Mapped[date | None]     = mapped_column(Date)
    comment                 : Mapped[str | None]      = mapped_column(Text)
    verification_file       : Mapped[str | None]      = mapped_column(String(512))

    created_at              : Mapped[datetime]        = mapped_column(DateTime, server_default=func.now())
    updated_at              : Mapped[datetime]        = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    project       : Mapped["Project"]              = relationship(back_populates="rpi_mappings")
    source_column : Mapped["MappingColumn | None"] = relationship(back_populates="rpi_mappings")