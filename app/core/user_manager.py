"""
Менеджер пользователей для fastapi-users.

Содержит:
- get_user_db: фабрика сессий БД для fastapi-users
- UserManager: хуки жизненного цикла пользователя
"""

import logging
from typing import Annotated

from fastapi import Depends, Request
from fastapi_users import BaseUserManager, IntegerIDMixin
from fastapi_users_db_sqlalchemy import SQLAlchemyUserDatabase

from app.core.config import settings
from app.database import AsyncSessionLocal
from app.models.user import User

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# User database adapter
# ---------------------------------------------------------------------------


async def get_user_db():
    """
    Зависимость, возвращающая SQLAlchemyUserDatabase для fastapi-users.

    Создаёт новую сессию БД на каждый запрос и оборачивает её в адаптер.
    """
    async with AsyncSessionLocal() as session:
        yield SQLAlchemyUserDatabase(session, User)


# ---------------------------------------------------------------------------
# User manager
# ---------------------------------------------------------------------------


class UserManager(IntegerIDMixin, BaseUserManager[User, int]):
    """
    Менеджер пользователей с хуками жизненного цикла.

    IntegerIDMixin добавляет корректную работу с int-идентификаторами.
    """

    reset_password_token_secret = settings.RESET_PASSWORD_TOKEN_SECRET
    verification_token_secret = settings.VERIFICATION_TOKEN_SECRET

    async def on_after_register(self, user: User, request: Request | None = None):
        """Хук после регистрации пользователя."""
        logger.info(f"User {user.id} ({user.email}) has registered.")

    async def on_after_forgot_password(
        self, user: User, token: str, request: Request | None = None
    ):
        """
        Хук после запроса сброса пароля.

        В production здесь должна быть отправка email.
        Сейчас просто логируем токен для отладки.
        """
        logger.info(
            f"User {user.id} ({user.email}) requested password reset. Token: {token}"
        )
        # В реальном приложении здесь отправка email:
        # send_reset_password_email(user.email, token)


# ---------------------------------------------------------------------------
# Dependency
# ---------------------------------------------------------------------------


async def get_user_manager(
    user_db: Annotated[SQLAlchemyUserDatabase, Depends(get_user_db)],
):
    """Зависимость FastAPI, возвращающая экземпляр UserManager."""
    yield UserManager(user_db)
