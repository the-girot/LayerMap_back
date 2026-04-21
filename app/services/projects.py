from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException
from app.models.project import Project
from app.schemas.project import ProjectCreate, ProjectUpdate
from app.core.cache import cache_get, cache_set, cache_delete, project_key, settings
from app.core.utils import handle_integrity
from app.schemas.project import ProjectOut

PROJECTS_LIST_KEY = "projects:list"


async def get_list(db: AsyncSession) -> list[Project]:
    cached = await cache_get(PROJECTS_LIST_KEY)
    if cached:
        # Восстанавливаем из dict обратно в Pydantic → или просто возвращаем dict-список
        return [Project(**item) for item in cached]

    rows = (
        await db.execute(select(Project).order_by(Project.created_at.desc()))
    ).scalars().all()

    # Сериализуем только чистые поля, без internal SA-атрибутов
    await cache_set(
        PROJECTS_LIST_KEY,
        [ProjectOut.model_validate(r).model_dump(mode="json") for r in rows],
        ttl=60,
    )
    return rows


async def get_one(db: AsyncSession, project_id: int) -> Project | None:
    key = project_key(project_id)
    cached = await cache_get(key)
    if cached:
        # Восстанавливаем plain dict → ORM-объект (без привязки к сессии)
        return Project(**cached)

    obj = (
        await db.execute(select(Project).where(Project.id == project_id))
    ).scalar_one_or_none()

    if obj:
        await cache_set(
            key,
            ProjectOut.model_validate(obj).model_dump(mode="json"),
            ttl=settings.CACHE_TTL,
        )
    return obj

async def create(db: AsyncSession, payload: ProjectCreate) -> Project:
    obj = Project(**payload.model_dump())
    db.add(obj)
    async with handle_integrity(db, f"Проект с именем '{payload.name}' уже существует"):
        await db.commit()
    await db.refresh(obj)
    await cache_delete(PROJECTS_LIST_KEY)
    return obj


async def update(db: AsyncSession, project_id: int, payload: ProjectUpdate) -> Project | None:
    obj = (
        await db.execute(select(Project).where(Project.id == project_id))
    ).scalar_one_or_none()
    if not obj:
        return None

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(obj, field, value)

    async with handle_integrity(db, f"Проект с именем '{payload.name}' уже существует"):
        await db.commit()

    await db.refresh(obj)
    await cache_delete(project_key(project_id), PROJECTS_LIST_KEY)
    return obj


async def delete(db: AsyncSession, project_id: int) -> bool:
    obj = (
        await db.execute(select(Project).where(Project.id == project_id))
    ).scalar_one_or_none()
    if not obj:
        return False

    await db.delete(obj)
    await db.commit()
    await cache_delete(project_key(project_id), PROJECTS_LIST_KEY)
    return True