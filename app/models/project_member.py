import enum
from datetime import UTC, datetime

from sqlalchemy import (
    DateTime,
    ForeignKey,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class ProjectRole(enum.StrEnum):
    owner = "owner"
    editor = "editor"
    viewer = "viewer"


class ProjectMember(Base):
    __tablename__ = "project_members"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    role: Mapped[ProjectRole] = mapped_column(
        String(50), nullable=False, default=ProjectRole.viewer
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=lambda: datetime.now(UTC),
    )

    user: Mapped["User"] = relationship(back_populates="project_memberships")
    project: Mapped["Project"] = relationship(back_populates="members")

    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "project_id",
            name="uq_project_members_user_project",
        ),
        {"sqlite_autoincrement": True},
    )

    def __repr__(self) -> str:
        return (
            f"<ProjectMember(user_id={self.user_id}, "
            f"project_id={self.project_id}, role={self.role})>"
        )
