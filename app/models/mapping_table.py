from datetime import datetime
from sqlalchemy import String, Text, ForeignKey, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base

class MappingTable(Base):
    __tablename__ = "mapping_tables"

    id          : Mapped[int]        = mapped_column(primary_key=True)
    project_id  : Mapped[int]        = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"))
    source_id   : Mapped[int | None] = mapped_column(ForeignKey("sources.id", ondelete="SET NULL"))
    name        : Mapped[str]        = mapped_column(String(255), nullable=False)
    description : Mapped[str | None] = mapped_column(Text)
    created_at  : Mapped[datetime]   = mapped_column(DateTime, server_default=func.now())
    updated_at  : Mapped[datetime]   = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    project : Mapped["Project"] = relationship(back_populates="mapping_tables")
    columns : Mapped[list["MappingColumn"]] = relationship(
        back_populates="mapping_table", cascade="all, delete-orphan"
    )