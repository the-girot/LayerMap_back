"""
Сервис для работы с пользователями.
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project_member import ProjectMember
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate


async def get_one(db: AsyncSession, user_id: int) -> User | None:
    """
    Получить пользователя по ID.

    Параметры:
        db: асинхронная сессия БД.
        user_id: ID пользователя.

    Возвращает:
        ORM-объект User или None.
    """
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


async def get_by_email(db: AsyncSession, email: str) -> User | None:
    """
    Получить пользователя по email.

    Параметры:
        db: асинхронная сессия БД.
        email: email пользователя.

    Возвращает:
        ORM-объект User или None.
    """
    result = await db.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


async def create(db: AsyncSession, payload: UserCreate) -> User:
    """
    Создать нового пользователя.

    Параметры:
        db: асинхронная сессия БД.
        payload: данные нового пользователя.

    Возвращает:
        Созданный ORM-объект User.
    """
    from app.core.security import get_password_hash

    hashed_password = get_password_hash(payload.password)
    user = User(
        email=payload.email,
        full_name=payload.full_name,
        hashed_password=hashed_password,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def update(
    db: AsyncSession,
    user_id: int,
    payload: UserUpdate,
) -> User | None:
    """
    Обновить пользователя.

    Параметры:
        db: асинхронная сессия БД.
        user_id: ID пользователя.
        payload: данные для обновления.

    Возвращает:
        Обновлённый ORM-объект User или None.
    """
    user = await get_one(db, user_id)
    if not user:
        return None

    update_data = payload.model_dump(exclude_unset=True)

    # Хешируем пароль только если он передан
    if "password" in update_data:
        from app.core.security import get_password_hash

        update_data["hashed_password"] = get_password_hash(update_data.pop("password"))

    for field, value in update_data.items():
        setattr(user, field, value)

    await db.commit()
    await db.refresh(user)
    return user


async def get_project_member(
    db: AsyncSession,
    *,
    user_id: int,
    project_id: int,
) -> ProjectMember | None:
    """
    Получить запись о членстве пользователя в проекте.

    Параметры:
        db: асинхронная сессия БД.
        user_id: ID пользователя.
        project_id: ID проекта.

    Возвращает:
        ORM-объект ProjectMember или None.
    """
    result = await db.execute(
        select(ProjectMember).where(
            ProjectMember.user_id == user_id,
            ProjectMember.project_id == project_id,
        )
    )
    return result.scalar_one_or_none()
