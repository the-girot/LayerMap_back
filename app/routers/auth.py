"""
Router аутентификации.

Эндпоинты:
- POST /auth/login - получение JWT токена (OAuth2PasswordRequestForm для Swagger)
- POST /auth/login/json - получение JWT токена (JSON для фронтенда)
- POST /auth/register - регистрация нового пользователя
- GET /auth/me - получение информации о текущем пользователе
- POST /auth/logout - выход из системы (очистка cookie)
"""

from fastapi import APIRouter, Depends, HTTPException, Response, status
from fastapi.security import OAuth2PasswordRequestForm

from app.core.auth import CurrentUser, DBSession
from app.core.config import settings
from app.core.security import create_access_token, verify_password
from app.schemas.user import Token, UserCreate, UserLogin, UserOut
from app.services import users as user_svc

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login", response_model=Token)
async def login_oauth2(
    db: DBSession,
    response: Response,
    form_data: OAuth2PasswordRequestForm = Depends(),
):
    """
    Войти в систему и получить JWT токен (OAuth2 для Swagger UI).

    Используется для авторизации через Swagger UI с кнопкой Authorize.
    Ожидает form-data: username (email) и password.

    Параметры:
        form_data: email и пароль пользователя из OAuth2PasswordRequestForm.
        db: асинхронная сессия БД.

    Возвращает:
        JWT токен для аутентификации.

    Исключения:
        HTTPException 401: если email или пароль неверны.
        HTTPException 403: если пользователь отключён.
    """

    # form_data.username содержит email (Swagger отправляет поле username)
    user = await user_svc.get_by_email(db, form_data.username)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный email или пароль",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Проверить пароль
    if not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный email или пароль",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Проверить, активен ли пользователь
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Пользователь отключён",
        )

    # Создать JWT токен
    access_token = create_access_token(data={"user_id": user.id})
    
    # Установить cookie с токеном
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=settings.COOKIE_SECURE,
        samesite=settings.COOKIE_SAMESITE,
        max_age=settings.COOKIE_MAX_AGE,
        path="/",
    )
    
    # Возвращаем токен для Swagger UI (кнопка Authorize)
    return Token(access_token=access_token, token_type="bearer")


@router.post("/login/json", response_model=dict)
async def login_json(
    payload: UserLogin,
    db: DBSession,
    response: Response,
):
    """
    Войти в систему и получить JWT токен (JSON для фронтенда).

    Ожидает JSON: {"email": "...", "password": "..."}

    Параметры:
        payload: email и пароль пользователя.
        db: асинхронная сессия БД.

    Возвращает:
        {"success": True} — токен устанавливается в httpOnly cookie.

    Исключения:
        HTTPException 401: если email или пароль неверны.
        HTTPException 403: если пользователь отключён.
    """

    # Найти пользователя по email
    user = await user_svc.get_by_email(db, payload.email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный email или пароль",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Проверить пароль
    if not verify_password(payload.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный email или пароль",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Проверить, активен ли пользователь
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Пользователь отключён",
        )

    # Создать JWT токен
    access_token = create_access_token(data={"user_id": user.id})
    
    # Установить cookie с токеном
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=settings.COOKIE_SECURE,
        samesite=settings.COOKIE_SAMESITE,
        max_age=settings.COOKIE_MAX_AGE,
        path="/",
    )
    
    # Для httpOnly cookie НЕ возвращаем токен в теле
    return {"success": True}


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def register(
    payload: UserCreate,
    db: DBSession,
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
            status_code=status.HTTP_409_CONFLICT,
            detail="Пользователь с таким email уже существует",
        )

    # Создать пользователя
    user = await user_svc.create(db, payload)

    return user


@router.get("/me", response_model=UserOut)
async def get_current_user_info(
    current_user: CurrentUser,  # просто тип, без лишнего Depends()
) -> UserOut:
    """
    Получить информацию о текущем аутентифицированном пользователе.

    Параметры:
        current_user: текущий пользователь, извлечённый из JWT токена.

    Возвращает:
        Объект пользователя.
    """
    return current_user


@router.post("/logout")
async def logout(response: Response):
    """
    Выйти из системы — очистить cookie с токеном.

    Возвращает:
        {"success": True}
    """
    response.set_cookie(
        key="access_token",
        value="",
        httponly=True,
        secure=settings.COOKIE_SECURE,
        samesite=settings.COOKIE_SAMESITE,
        max_age=0,
        expires=0,
        path="/",
    )
    return {"success": True}
