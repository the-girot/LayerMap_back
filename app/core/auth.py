"""
Аутентификация и авторизация через fastapi-users.

Содержит:
- Настройку JWT-аутентификации (BearerTransport + JWTStrategy)
- FastAPIUsers — центральный объект библиотеки
- Зависимости current_active_user, current_superuser
- require_project_role — фабрика для проверки прав доступа к проекту
"""

import logging
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi_users import FastAPIUsers
from fastapi_users.authentication import (
    AuthenticationBackend,
    CookieTransport,  # ← вместо BearerTransport
    JWTStrategy,
)

from app.core.config import settings
from app.core.user_manager import get_user_manager
from app.database import DBSession
from app.models.project import Project
from app.models.project_member import ProjectRole
from app.models.user import User
from app.services import projects as project_svc
from app.services import users as user_svc

logger = logging.getLogger(__name__)

# ─── Cookie transport ───────────────────────────────────────────────────────

cookie_transport = CookieTransport(
    cookie_name="layermap_access",
    cookie_max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    cookie_secure=False,  # только HTTPS (в dev можно False)
    cookie_httponly=True,  # недоступен из JS
    cookie_samesite="lax",  # защита от CSRF
)

# ─── JWT strategy ───────────────────────────────────────────────────────────


def get_jwt_strategy() -> JWTStrategy:
    return JWTStrategy(
        secret=settings.JWT_SECRET_KEY,
        lifetime_seconds=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


# ─── Auth backend ───────────────────────────────────────────────────────────

auth_backend = AuthenticationBackend(
    name="jwt",
    transport=cookie_transport,  # ← было bearer_transport
    get_strategy=get_jwt_strategy,
)

# ---------------------------------------------------------------------------
# FastAPIUsers — центральный объект
# ---------------------------------------------------------------------------

fastapi_users = FastAPIUsers[User, int](
    get_user_manager=get_user_manager,
    auth_backends=[auth_backend],
)

# ---------------------------------------------------------------------------
# Зависимости для роутеров
# ---------------------------------------------------------------------------

current_active_user = fastapi_users.current_user(active=True)
current_superuser = fastapi_users.current_user(active=True, superuser=True)

# Type alias для удобного использования в роутерах
CurrentUser = Annotated[User, Depends(current_active_user)]
CurrentSuperuser = Annotated[User, Depends(current_superuser)]

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
