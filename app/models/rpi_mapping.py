import enum
from datetime import UTC, date, datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.source_table import (
    SourceColumn,
)


class RPIStatus(enum.StrEnum):
    approved = "approved"
    in_review = "in_review"
    draft = "draft"


class MeasurementType(enum.StrEnum):
    dimension = "dimension"
    metric = "metric"


class RPIMapping(Base):
    __tablename__ = "rpi_mappings"
    __table_args__ = (
        CheckConstraint(
            "(is_calculated = TRUE AND formula IS NOT NULL) OR (is_calculated = FALSE)",
            name="chk_formula",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    number: Mapped[int | None] = mapped_column(Integer)
    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE")
    )
    source_column_id: Mapped[int | None] = mapped_column(
        ForeignKey("source_columns.id", ondelete="SET NULL")
    )

    ownership: Mapped[str | None] = mapped_column(String(128))
    status: Mapped[RPIStatus] = mapped_column(Enum(RPIStatus), default=RPIStatus.draft)
    block: Mapped[str | None] = mapped_column(String(128))
    measurement_type: Mapped[MeasurementType | None] = mapped_column(
        Enum(MeasurementType), nullable=True
    )
    is_calculated: Mapped[bool] = mapped_column(Boolean, server_default="false")
    formula: Mapped[str | None] = mapped_column(Text)

    dimension: Mapped[str | None] = mapped_column(String(255), nullable=True)
    measurement: Mapped[str] = mapped_column(String(255), nullable=False)
    measurement_description: Mapped[str | None] = mapped_column(Text)
    source_report: Mapped[str | None] = mapped_column(String(255))
    object_field: Mapped[str] = mapped_column(String(255), nullable=False)

    date_added: Mapped[date | None] = mapped_column(Date)
    date_removed: Mapped[date | None] = mapped_column(Date)
    comment: Mapped[str | None] = mapped_column(Text)
    verification_file: Mapped[str | None] = mapped_column(String(512))

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=lambda: datetime.now(UTC),
    )

    project: Mapped["Project"] = relationship(back_populates="rpi_mappings")
    source_column: Mapped["SourceColumn | None"] = relationship(
        "SourceColumn",
        back_populates="rpi_mappings",
        foreign_keys="[RPIMapping.source_column_id]"
    )
