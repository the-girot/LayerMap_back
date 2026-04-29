"""
Pydantic схемы для модели User, унаследованные от fastapi-users.
"""

from fastapi_users import schemas
from pydantic import EmailStr


class UserRead(schemas.BaseUser[int]):
    """
    Схема чтения пользователя.

    Включает все поля BaseUser (id, email, is_active, is_superuser, is_verified)
    плюс кастомное full_name.
    """

    full_name: str | None = None

    model_config = {"from_attributes": True}


class UserCreate(schemas.BaseUserCreate):
    """
    Схема создания пользователя.

    Включает email, password, is_active, is_superuser, is_verified
    плюс кастомное full_name.
    """

    full_name: str | None = None


class UserUpdate(schemas.BaseUserUpdate):
    """
    Схема обновления пользователя.

    Все поля опциональны (PATCH-семантика).
    """

    full_name: str | None = None
