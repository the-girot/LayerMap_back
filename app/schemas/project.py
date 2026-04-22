from datetime import datetime

from pydantic import BaseModel

from app.models.project import ProjectStatus


class ProjectBase(BaseModel):
    """
    Базовые поля проекта, общие для операций создания и чтения.
    """

    name: str
    description: str | None = None
    status: ProjectStatus = ProjectStatus.draft


class ProjectCreate(ProjectBase):
    """
    Схема для создания проекта.
    """

    pass


class ProjectUpdate(BaseModel):
    """
    Схема частичного обновления проекта.

    Все поля являются необязательными и применяются по принципу PATCH.
    """

    name: str | None = None
    description: str | None = None
    status: ProjectStatus | None = None


class ProjectOut(ProjectBase):
    """
    Полное представление проекта, возвращаемое из API.
    """

    id: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ProjectKPIOut(BaseModel):
    """
    Агрегированные KPI по проектам для дашборда.

    Поля:
        total: общее количество проектов.
        active: количество активных проектов.
        draft: количество проектов в статусе черновика.
        archived: количество архивных проектов.
    """

    total: int
    active: int
    draft: int
    archived: int


class ProjectSummaryOut(BaseModel):
    """
    Краткая информация о проекте для списка последних проектов на дашборде.

    Поля:
        id: идентификатор проекта.
        name: название проекта.
        status: текущий статус проекта.
        updated_at: дата и время последнего обновления.
    """

    id: int
    name: str
    status: ProjectStatus
    updated_at: datetime

    model_config = {"from_attributes": True}
