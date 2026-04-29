"""
Роутер аутентификации.

Содержит все эндпоинты аутентификации и авторизации через fastapi-users:

  POST /auth/jwt/login          — логин (JWT)
  POST /auth/register           — регистрация
  POST /auth/forgot-password    — запрос сброса пароля
  POST /auth/reset-password     — сброс пароля
  GET  /users/me                — текущий пользователь
  PATCH /users/me               — обновление профиля
  GET  /users/{id}              — получение пользователя по ID
  PATCH /users/{id}             — обновление пользователя (админ)
  DELETE /users/{id}            — удаление пользователя (админ)
"""

from fastapi import APIRouter

from app.core.auth import auth_backend, fastapi_users
from app.schemas.user import UserCreate, UserRead, UserUpdate


def get_auth_router() -> APIRouter:
    """
    Фабрика роутера аутентификации.

    Возвращает APIRouter со всеми эндпоинтами fastapi-users.
    Это позволяет инкапсулировать логику аутентификации в одном месте.
    """
    router = APIRouter()

    # JWT login
    router.include_router(
        fastapi_users.get_auth_router(auth_backend),
        prefix="/auth/jwt",
        tags=["auth"],
    )

    # Регистрация
    router.include_router(
        fastapi_users.get_register_router(UserRead, UserCreate),
        prefix="/auth",
        tags=["auth"],
    )

    # Сброс пароля
    router.include_router(
        fastapi_users.get_reset_password_router(),
        prefix="/auth",
        tags=["auth"],
    )

    # CRUD пользователей
    router.include_router(
        fastapi_users.get_users_router(UserRead, UserUpdate),
        prefix="/users",
        tags=["users"],
    )

    return router
