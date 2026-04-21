from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.source import Source
from app.schemas.source import SourceCreate, SourceUpdate
from app.core.cache import (
    cache_get, cache_set, cache_delete,
    sources_key, settings
)


async def get_list(db: AsyncSession, project_id: int) -> list[Source]:
    key = sources_key(project_id)
    cached = await cache_get(key)
    if cached:
        return cached

    rows = (
        await db.execute(
            select(Source)
            .where(Source.project_id == project_id)
            .order_by(Source.id)
        )
    ).scalars().all()

    await cache_set(key, [r.__dict__ for r in rows], ttl=settings.CACHE_TTL)
    return rows


async def get_one(db: AsyncSession, project_id: int, source_id: int) -> Source | None:
    key = f"project:{project_id}:source:{source_id}"
    cached = await cache_get(key)
    if cached:
        return cached

    obj = (
        await db.execute(
            select(Source).where(
                Source.id == source_id,
                Source.project_id == project_id,
            )
        )
    ).scalar_one_or_none()

    if obj:
        await cache_set(key, obj.__dict__, ttl=settings.CACHE_TTL)
    return obj


async def create(db: AsyncSession, project_id: int, payload: SourceCreate) -> Source:
    obj = Source(**payload.model_dump(), project_id=project_id)
    db.add(obj)
    await db.commit()
    await db.refresh(obj)
    await cache_delete(sources_key(project_id))
    return obj


async def update(
    db: AsyncSession, project_id: int, source_id: int, payload: SourceUpdate
) -> Source | None:
    obj = (
        await db.execute(
            select(Source).where(
                Source.id == source_id,
                Source.project_id == project_id,
            )
        )
    ).scalar_one_or_none()
    if not obj:
        return None

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(obj, field, value)

    await db.commit()
    await db.refresh(obj)
    await cache_delete(
        sources_key(project_id),
        f"project:{project_id}:source:{source_id}",
    )
    return obj


async def delete(db: AsyncSession, project_id: int, source_id: int) -> bool:
    obj = (
        await db.execute(
            select(Source).where(
                Source.id == source_id,
                Source.project_id == project_id,
            )
        )
    ).scalar_one_or_none()
    if not obj:
        return False

    await db.delete(obj)
    await db.commit()
    await cache_delete(
        sources_key(project_id),
        f"project:{project_id}:source:{source_id}",
    )
    return True