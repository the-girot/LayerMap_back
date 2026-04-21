import enum
from datetime import datetime
from sqlalchemy import String, Text, Enum, BigInteger, ForeignKey, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base

class SourceType(str, enum.Enum):
    API    = "API"
    DB     = "DB"
    FILE   = "FILE"
    STREAM = "STREAM"

class Source(Base):
    __tablename__ = "sources"

    id               : Mapped[int]            = mapped_column(primary_key=True)
    project_id       : Mapped[int]            = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"))
    mapping_table_id : Mapped[int | None]     = mapped_column(ForeignKey("mapping_tables.id", ondelete="SET NULL"))
    name             : Mapped[str]            = mapped_column(String(255), nullable=False)
    description      : Mapped[str | None]     = mapped_column(Text)
    type             : Mapped[SourceType]     = mapped_column(Enum(SourceType), default=SourceType.DB)
    row_count        : Mapped[int]            = mapped_column(BigInteger, default=0)
    last_updated     : Mapped[datetime | None]= mapped_column(DateTime)
    created_at       : Mapped[datetime]       = mapped_column(DateTime, server_default=func.now())

    project       : Mapped["Project"]            = relationship(back_populates="sources")
    mapping_table : Mapped["MappingTable | None"]= relationship(foreign_keys=[mapping_table_id])