import enum
from datetime import datetime
from sqlalchemy import String, Text, Enum, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base

class ProjectStatus(str, enum.Enum):
    active   = "active"
    draft    = "draft"
    archived = "archived"

class Project(Base):
    __tablename__ = "projects"

    id          : Mapped[int]           = mapped_column(primary_key=True)
    name        : Mapped[str]           = mapped_column(String(255), nullable=False, unique=True)
    description : Mapped[str | None]    = mapped_column(Text)
    status      : Mapped[ProjectStatus] = mapped_column(
                      Enum(ProjectStatus), default=ProjectStatus.draft
                  )
    created_at  : Mapped[datetime]      = mapped_column(DateTime, server_default=func.now())
    updated_at  : Mapped[datetime]      = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    sources         : Mapped[list["Source"]]       = relationship(back_populates="project", cascade="all, delete-orphan")
    mapping_tables  : Mapped[list["MappingTable"]] = relationship(back_populates="project", cascade="all, delete-orphan")
    rpi_mappings    : Mapped[list["RPIMapping"]]   = relationship(back_populates="project", cascade="all, delete-orphan")