"""
Pydantic схемы для модели User.
"""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, EmailStr, Field


class UserBase(BaseModel):
    """
    Базовые поля пользователя, общие для операций создания и чтения.
    """

    email: EmailStr = Field(..., description="Email адрес пользователя")
    full_name: str | None = Field(None, description="Полное имя пользователя")


class UserCreate(UserBase):
    """
    Схема для создания пользователя.
    """

    password: str = Field(..., min_length=8, description="Пароль (минимум 8 символов)")


class UserUpdate(BaseModel):
    """
    Схема частичного обновления пользователя.

    Все поля являются необязательными и применяются по принципу PATCH.
    """

    email: EmailStr | None = None
    full_name: str | None = None
    password: str | None = Field(
        None, min_length=8, description="Новый пароль (минимум 8 символов)"
    )
    is_active: bool | None = None
    is_superuser: bool | None = None


class UserOut(UserBase):
    """
    Полное представление пользователя, возвращаемое из API.
    """

    id: int = Field(..., description="ID пользователя")
    is_active: bool = Field(..., description="Активен ли пользователь")
    is_superuser: bool = Field(..., description="Является ли суперпользователем")
    # status: UserStatus = Field(..., description="Статус пользователя")
    created_at: datetime = Field(..., description="Дата создания")
    updated_at: datetime = Field(..., description="Дата обновления")

    model_config = {"from_attributes": True}


class UserLogin(BaseModel):
    """
    Схема для входа пользователя (логин/пароль).
    """

    email: str = Field(..., description="Email адрес пользователя")
    password: str = Field(..., description="Пароль")


class Token(BaseModel):
    """
    Схема ответа с токеном аутентификации.
    """

    access_token: str = Field(..., description="JWT токен для аутентификации")
    token_type: Literal["bearer"] = Field("bearer", description="Тип токена")


class TokenData(BaseModel):
    """
    Схема данных токена (для валидации).
    """

    user_id: int | None = None
