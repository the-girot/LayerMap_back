from fastapi import HTTPException
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.cache import (
    cache_delete,
    cache_delete_pattern,
    cache_get,
    cache_set,
    hash_params,
    rpi_list_key,
    rpi_stats_key,
    settings,
)
from app.models.rpi_mapping import RPIMapping, RPIStatus
from app.models.source_table import SourceColumn
from app.schemas.rpi_mapping import RPIMappingCreate, RPIMappingUpdate, RPIStatsOut


# ── Инвалидация всего кэша проекта ────────────────────────────
async def _invalidate(project_id: int):
    await cache_delete_pattern(f"project:{project_id}:rpi:*")


# ── Список с фильтрами ─────────────────────────────────────────
async def get_list(
    db: AsyncSession,
    project_id: int,
    *,
    status: str | None = None,
    ownership: str | None = None,
    measurement_type: str | None = None,
    dimension: str | None = None,
    is_calculated: bool | None = None,
    search: str | None = None,
    skip: int = 0,
    limit: int = 20,
) -> list[RPIMapping]:
    params_hash = hash_params(
        status=status,
        ownership=ownership,
        measurement_type=measurement_type,
        dimension=dimension,
        is_calculated=is_calculated,
        search=search,
        skip=skip,
        limit=limit,
    )
    key = rpi_list_key(project_id, params_hash)
    cached = await cache_get(key)
    if cached is not None:
        return cached

    q = (
        select(RPIMapping)
        .where(RPIMapping.project_id == project_id)
        .options(selectinload(RPIMapping.source_column))  # избегаем N+1
    )
    if status:
        q = q.where(RPIMapping.status == status)
    if ownership:
        q = q.where(RPIMapping.ownership == ownership)
    if measurement_type:
        q = q.where(RPIMapping.measurement_type == measurement_type)
    if dimension:
        q = q.where(RPIMapping.dimension.ilike(f"%{dimension}%"))
    if is_calculated is not None:
        q = q.where(RPIMapping.is_calculated == is_calculated)
    if search:
        like = f"%{search}%"
        q = q.where(
            or_(
                RPIMapping.measurement.ilike(like),
                RPIMapping.dimension.ilike(like),
                RPIMapping.object_field.ilike(like),
                RPIMapping.ownership.ilike(like),
            )
        )
    q = q.order_by(RPIMapping.number).offset(skip).limit(limit)

    rows = (await db.execute(q)).scalars().all()
    # Кэшируем как list[dict] (не ORM объекты)
    await cache_set(key, [r.__dict__ for r in rows], ttl=60)
    return rows


# ── Статистика ─────────────────────────────────────────────────
async def get_stats(db: AsyncSession, project_id: int) -> RPIStatsOut:
    key = rpi_stats_key(project_id)
    cached = await cache_get(key)
    if cached:
        return RPIStatsOut(**cached)

    # Один агрегатный запрос вместо нескольких COUNT
    q = (
        select(RPIMapping.status, func.count().label("cnt"))
        .where(RPIMapping.project_id == project_id)
        .group_by(RPIMapping.status)
    )
    rows = (await db.execute(q)).all()
    counts = {r.status: r.cnt for r in rows}
    total = sum(counts.values())

    stats = RPIStatsOut(
        total=total,
        approved=counts.get(RPIStatus.approved, 0),
        in_review=counts.get(RPIStatus.in_review, 0),
        draft=counts.get(RPIStatus.draft, 0),
    )
    await cache_set(key, stats.model_dump(), ttl=120)
    return stats


# ── Одна запись ────────────────────────────────────────────────
async def get_one(db: AsyncSession, project_id: int, rpi_id: int) -> RPIMapping | None:
    key = f"project:{project_id}:rpi:{rpi_id}"
    cached = await cache_get(key)
    if cached:
        return RPIMapping(**{k: v for k, v in cached.items() if not k.startswith("_")})

    q = (
        select(RPIMapping)
        .where(RPIMapping.id == rpi_id, RPIMapping.project_id == project_id)
        .options(selectinload(RPIMapping.source_column))
    )
    obj = (await db.execute(q)).scalar_one_or_none()
    if obj:
        await cache_set(key, obj.__dict__, ttl=settings.CACHE_TTL)
    return obj


# ── Создание ──────────────────────────────────────────────────
async def create(db: AsyncSession, project_id: int, payload: RPIMappingCreate) -> RPIMapping:
    # Валидируем source_column_id до INSERT
    if payload.source_column_id is not None:
        col = (
            await db.execute(
                select(SourceColumn).where(SourceColumn.id == payload.source_column_id)
            )
        ).scalar_one_or_none()
        if col is None:
            raise HTTPException(404, f"Колонка source_column_id={payload.source_column_id} не найдена")

    max_num = await db.scalar(
        select(func.coalesce(func.max(RPIMapping.number), 0)).where(
            RPIMapping.project_id == project_id
        )
    )
    obj = RPIMapping(**payload.model_dump(), project_id=project_id, number=max_num + 1)
    db.add(obj)
    await db.commit()
    await db.refresh(obj)
    await _invalidate(project_id)
    return obj


# ── Обновление ────────────────────────────────────────────────
async def update(
    db: AsyncSession, project_id: int, rpi_id: int, payload: RPIMappingUpdate
) -> RPIMapping | None:
    # Always query DB directly — cached objects from get_one() are detached
    # and would fail on db.refresh() with "not persistent within this Session"
    q = select(RPIMapping).where(
        RPIMapping.id == rpi_id, RPIMapping.project_id == project_id
    )
    obj = (await db.execute(q)).scalar_one_or_none()
    if not obj:
        return None

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(obj, field, value)

    await db.commit()
    await db.refresh(obj)
    await _invalidate(project_id)
    await cache_delete(f"project:{project_id}:rpi:{rpi_id}")
    return obj


# ── Удаление ──────────────────────────────────────────────────
async def delete(db: AsyncSession, project_id: int, rpi_id: int) -> bool:
    q = select(RPIMapping).where(
        RPIMapping.id == rpi_id, RPIMapping.project_id == project_id
    )
    obj = (await db.execute(q)).scalar_one_or_none()
    if not obj:
        return False
    await db.delete(obj)
    await db.commit()
    await _invalidate(project_id)
    await cache_delete(f"project:{project_id}:rpi:{rpi_id}")
    return True
