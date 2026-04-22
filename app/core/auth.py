from typing import Annotated

from fastapi import Depends, HTTPException, status

from app.core.security import decode_token, oauth2_scheme
from app.database import DBSession
from app.models.project import Project
from app.models.project_member import ProjectRole
from app.models.user import User
from app.services import projects as project_svc
from app.services import users as user_svc

# ---------------------------------------------------------------------------
# get_current_user
# ---------------------------------------------------------------------------


async def get_current_user(
    db: DBSession,
    token: Annotated[str, Depends(oauth2_scheme)],
) -> User:
    payload = decode_token(token)
    if not payload or "user_id" not in payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Невалидный токен",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id: int = payload["user_id"]
    user = await user_svc.get_one(db, user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Пользователь не найден",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Пользователь отключён",
        )

    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


async def get_current_active_superuser(
    current_user: CurrentUser,
) -> User:
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Требуется доступ суперпользователя.",
        )
    return current_user


CurrentSuperuser = Annotated[User, Depends(get_current_active_superuser)]


# ---------------------------------------------------------------------------
# ACL: фабрика зависимостей для проекта
# ---------------------------------------------------------------------------

_PERMISSION_ORDER = [ProjectRole.viewer, ProjectRole.editor, ProjectRole.owner]


def require_project_role(required_role: ProjectRole):
    """
    Фабрика зависимостей: возвращает замыкание, которое проверяет,
    что текущий пользователь имеет нужную роль в проекте.

    Использование:
        project: Annotated[Project, Depends(require_project_role(ProjectRole.editor))]
    """

    async def dependency(
        project_id: int,
        db: DBSession,
        current_user: CurrentUser,
    ) -> Project:
        # Загрузить проект (404 если не существует)
        project = await project_svc.get_one(db, project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Проект не найден")

        # Суперпользователь имеет полный доступ
        if current_user.is_superuser:
            return project

        # Получить membership
        member = await user_svc.get_project_member(
            db=db,
            user_id=current_user.id,
            project_id=project.id,
        )

        if not member:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="У вас нет доступа к этому проекту",
            )

        # Проверка иерархии ролей
        user_level = _PERMISSION_ORDER.index(member.role)
        required_level = _PERMISSION_ORDER.index(required_role)

        if user_level < required_level:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Требуется роль: {required_role.value}",
            )

        return project

    return dependency


# Алиасы для удобного использования в роутерах
ProjectViewer = Annotated[Project, Depends(require_project_role(ProjectRole.viewer))]
ProjectEditor = Annotated[Project, Depends(require_project_role(ProjectRole.editor))]
ProjectOwner = Annotated[Project, Depends(require_project_role(ProjectRole.owner))]
