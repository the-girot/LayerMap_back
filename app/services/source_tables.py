from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.cache import (
    cache_delete,
    cache_get,
    cache_set,
    settings,
)
from app.models.source_table import SourceColumn, SourceTable
from app.schemas.source_table import (
    SourceColumnCreate,
    SourceColumnOut,
    SourceColumnUpdate,
    SourceTableCreate,
    SourceTableOut,
    SourceTableUpdate,
)

# ── Таблицы ──────────────────────────────────────────────────────────────────


async def get_list(db: AsyncSession, source_id: int) -> list[SourceTableOut]:
    key = f"source_tables:{source_id}"
    cached = await cache_get(key)
    if cached:
        return [SourceTableOut.model_validate(r) for r in cached]

    rows = (
        (
            await db.execute(
                select(SourceTable)
                .where(SourceTable.source_id == source_id)
                .options(selectinload(SourceTable.columns))
                .order_by(SourceTable.id)
            )
        )
        .scalars()
        .all()
    )

    result = [SourceTableOut.model_validate(r) for r in rows]
    await cache_set(
        key,
        [SourceTableOut.model_validate(r).model_dump(mode="json") for r in rows],
        ttl=60,
    )
    return result


async def get_one(
    db: AsyncSession, source_id: int, table_id: int
) -> SourceTableOut | None:
    key = f"source_table:{table_id}"
    cached = await cache_get(key)
    if cached:
        return SourceTableOut.model_validate(cached)

    obj = (
        await db.execute(
            select(SourceTable)
            .where(
                SourceTable.id == table_id,
                SourceTable.source_id == source_id,
            )
            .options(selectinload(SourceTable.columns))
        )
    ).scalar_one_or_none()

    if obj:
        result = SourceTableOut.model_validate(obj)
        await cache_set(key, result.model_dump(), ttl=settings.CACHE_TTL)
        return result
    return None


async def create(
    db: AsyncSession,
    source_id: int,
    payload: SourceTableCreate,
) -> SourceTableOut:
    obj = SourceTable(**payload.model_dump(), source_id=source_id)
    db.add(obj)
    await db.commit()
    await db.refresh(obj)
    await db.refresh(obj, attribute_names=["columns"])
    await cache_delete(f"source_tables:{source_id}")

    result = SourceTableOut.model_validate(obj)
    return result


async def update(
    db: AsyncSession, source_id: int, table_id: int, payload: SourceTableUpdate
) -> SourceTableOut | None:
    obj = (
        await db.execute(
            select(SourceTable).where(
                SourceTable.id == table_id,
                SourceTable.source_id == source_id,
            )
        )
    ).scalar_one_or_none()
    if not obj:
        return None

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(obj, field, value)

    await db.commit()
    await db.refresh(obj)
    await db.refresh(obj, attribute_names=["columns"])
    await cache_delete(
        f"source_tables:{source_id}",
        f"source_table:{table_id}",
        f"source_columns:{table_id}",
    )

    return SourceTableOut.model_validate(obj)


async def delete(db: AsyncSession, source_id: int, table_id: int) -> bool:
    obj = (
        await db.execute(
            select(SourceTable).where(
                SourceTable.id == table_id,
                SourceTable.source_id == source_id,
            )
        )
    ).scalar_one_or_none()
    if not obj:
        return False

    await db.delete(obj)
    await db.commit()
    await cache_delete(
        f"source_tables:{source_id}",
        f"source_table:{table_id}",
        f"source_columns:{table_id}",
    )
    return True


# ── Колонки ──────────────────────────────────────────────────────────────────


async def get_columns(db: AsyncSession, table_id: int) -> list[SourceColumnOut]:
    key = f"source_columns:{table_id}"
    cached = await cache_get(key)
    if cached:
        return [SourceColumnOut.model_validate(r) for r in cached]

    rows = (
        (
            await db.execute(
                select(SourceColumn)
                .where(SourceColumn.source_table_id == table_id)
                .order_by(SourceColumn.id)
            )
        )
        .scalars()
        .all()
    )

    result = [SourceColumnOut.model_validate(r) for r in rows]
    await cache_set(key, [r.model_dump() for r in result], ttl=settings.CACHE_TTL)
    return result


async def get_column(
    db: AsyncSession, table_id: int, column_id: int
) -> SourceColumnOut | None:
    key = f"source_column:{table_id}:{column_id}"
    cached = await cache_get(key)
    if cached:
        return SourceColumnOut.model_validate(cached)

    obj = (
        await db.execute(
            select(SourceColumn).where(
                SourceColumn.id == column_id,
                SourceColumn.source_table_id == table_id,
            )
        )
    ).scalar_one_or_none()

    if obj:
        result = SourceColumnOut.model_validate(obj)
        await cache_set(key, result.model_dump(), ttl=settings.CACHE_TTL)
        return result
    return None


async def create_column(
    db: AsyncSession, table_id: int, payload: SourceColumnCreate
) -> SourceColumnOut:
    obj = SourceColumn(**payload.model_dump(), source_table_id=table_id)
    db.add(obj)
    await db.commit()
    await db.refresh(obj)
    await cache_delete(f"source_columns:{table_id}")
    return SourceColumnOut.model_validate(obj)


async def update_column(
    db: AsyncSession, table_id: int, column_id: int, payload: SourceColumnUpdate
) -> SourceColumnOut | None:
    obj = (
        await db.execute(
            select(SourceColumn).where(
                SourceColumn.id == column_id,
                SourceColumn.source_table_id == table_id,
            )
        )
    ).scalar_one_or_none()
    if not obj:
        return None

    update_data = payload.model_dump(exclude_unset=True)

    # Кросс-полевая валидация: мёржим текущее состояние с патчем
    merged_is_calculated = update_data.get("is_calculated", obj.is_calculated)
    merged_formula = update_data.get("formula", obj.formula)

    if merged_is_calculated and not merged_formula:
        raise HTTPException(
            status_code=422,
            detail=[
                {
                    "loc": ["body", "formula"],
                    "msg": "formula обязательна когда is_calculated=True",
                    "type": "value_error.missing",
                }
            ],
        )

    for field, value in update_data.items():
        setattr(obj, field, value)

    await db.commit()
    await db.refresh(obj)
    await cache_delete(
        f"source_columns:{table_id}",
        f"source_column:{table_id}:{column_id}",
    )
    return SourceColumnOut.model_validate(obj)


async def delete_column(db: AsyncSession, table_id: int, column_id: int) -> bool:
    obj = (
        await db.execute(
            select(SourceColumn).where(
                SourceColumn.id == column_id,
                SourceColumn.source_table_id == table_id,
            )
        )
    ).scalar_one_or_none()
    if not obj:
        return False

    await db.delete(obj)
    await db.commit()
    await cache_delete(
        f"source_columns:{table_id}",
        f"source_column:{table_id}:{column_id}",
    )
    return True
