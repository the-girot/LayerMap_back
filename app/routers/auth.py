"""
Router аутентификации.

Эндпоинты:
- POST /auth/login - получение JWT токена
- POST /auth/register - регистрация нового пользователя
- GET /auth/me - получение информации о текущем пользователе
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import CurrentUser, DBSession
from app.core.security import create_access_token, verify_password
from app.models.user import User
from app.schemas.user import Token, UserCreate, UserLogin, UserOut
from app.services import users as user_svc

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login", response_model=Token)
async def login(
    payload: UserLogin,
    db: Annotated[AsyncSession, Depends(DBSession)],
):
    """
    Войти в систему и получить JWT токен.

    Параметры:
        payload: email и пароль пользователя.
        db: асинхронная сессия БД.

    Возвращает:
        JWT токен для аутентификации.

    Исключения:
        HTTPException 400: если email или пароль неверны.
    """

    # Найти пользователя по email
    user = await user_svc.get_by_email(db, payload.email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Неверный email или пароль",
        )

    # Проверить пароль
    if not verify_password(payload.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Неверный email или пароль",
        )

    # Проверить, активен ли пользователь
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Пользователь отключён",
        )

    # Создать JWT токен
    access_token_expires = None  # Используем дефолтное время из config
    access_token = create_access_token(
        data={"user_id": user.id},
        expires_delta=access_token_expires,
    )

    return Token(access_token=access_token, token_type="bearer")


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def register(
    payload: UserCreate,
    db: Annotated[AsyncSession, Depends(DBSession)],
):
    """
    Зарегистрировать нового пользователя.

    Параметры:
        payload: email, пароль и опционально полное имя.
        db: асинхронная сессия БД.

    Возвращает:
        Созданный объект пользователя.

    Исключения:
        HTTPException 400: если email уже занят.
    """

    # Проверить, существует ли пользователь с таким email
    existing_user = await user_svc.get_by_email(db, payload.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Пользователь с таким email уже существует",
        )

    # Создать пользователя
    user = await user_svc.create(db, payload)

    return UserOut(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        is_active=user.is_active,
        is_superuser=user.is_superuser,
        status=user.status,
        created_at=user.created_at,
        updated_at=user.updated_at,
    )


@router.get("/me", response_model=UserOut)
async def get_current_user_info(
    current_user: Annotated[User, Depends(CurrentUser)],
) -> UserOut:
    """
    Получить информацию о текущем аутентифицированном пользователе.

    Параметры:
        current_user: текущий пользователь, извлечённый из JWT токена.

    Возвращает:
        Объект пользователя.
    """
    return UserOut(
        id=current_user.id,
        email=current_user.email,
        full_name=current_user.full_name,
        is_active=current_user.is_active,
        is_superuser=current_user.is_superuser,
        status=current_user.status,
        created_at=current_user.created_at,
        updated_at=current_user.updated_at,
    )
