from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.models.mapping_table import MappingTable
from app.models.rpi_mapping import MappingColumn
from app.schemas.mapping_table import (
    MappingTableCreate, MappingTableUpdate, MappingTableOut,
    MappingColumnCreate, MappingColumnUpdate, MappingColumnOut,
)
from app.core.cache import (
    cache_get, cache_set, cache_delete, cache_delete_pattern,
    mapping_tables_key, settings
)


# ── Таблицы ───────────────────────────────────────────────────
async def get_list(db: AsyncSession, project_id: int) -> list[MappingTableOut]:
    key = mapping_tables_key(project_id)
    cached = await cache_get(key)
    if cached:
        return [MappingTableOut.model_validate(r) for r in cached]

    rows = (
        await db.execute(
            select(MappingTable)
            .where(MappingTable.project_id == project_id)
            .options(selectinload(MappingTable.columns))
            .order_by(MappingTable.id)
        )
    ).scalars().all()

    result = [MappingTableOut.model_validate(r) for r in rows]
    await cache_set(key, [r.model_dump() for r in result], ttl=settings.CACHE_TTL)
    return result


async def get_one(db: AsyncSession, project_id: int, table_id: int) -> MappingTableOut | None:
    key = f"project:{project_id}:mapping_table:{table_id}"
    cached = await cache_get(key)
    if cached:
        return MappingTableOut.model_validate(cached)

    obj = (
        await db.execute(
            select(MappingTable)
            .where(
                MappingTable.id == table_id,
                MappingTable.project_id == project_id,
            )
            .options(selectinload(MappingTable.columns))
        )
    ).scalar_one_or_none()

    if obj:
        result = MappingTableOut.model_validate(obj)
        await cache_set(key, result.model_dump(), ttl=settings.CACHE_TTL)
        return result
    return None


async def create(db: AsyncSession, project_id: int, payload: MappingTableCreate) -> MappingTableOut:
    obj = MappingTable(**payload.model_dump(), project_id=project_id)
    db.add(obj)
    await db.commit()
    await db.refresh(obj)
    await db.refresh(obj, attribute_names=["columns"])
    await cache_delete(mapping_tables_key(project_id))
    return MappingTableOut.model_validate(obj)


async def update(
    db: AsyncSession, project_id: int, table_id: int, payload: MappingTableUpdate
) -> MappingTableOut | None:
    obj = (
        await db.execute(
            select(MappingTable).where(
                MappingTable.id == table_id,
                MappingTable.project_id == project_id,
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
        mapping_tables_key(project_id),
        f"project:{project_id}:mapping_table:{table_id}",
    )
    return MappingTableOut.model_validate(obj)


async def delete(db: AsyncSession, project_id: int, table_id: int) -> bool:
    obj = (
        await db.execute(
            select(MappingTable).where(
                MappingTable.id == table_id,
                MappingTable.project_id == project_id,
            )
        )
    ).scalar_one_or_none()
    if not obj:
        return False

    await db.delete(obj)
    await db.commit()
    await cache_delete(
        mapping_tables_key(project_id),
        f"project:{project_id}:mapping_table:{table_id}",
    )
    return True


# ── Колонки ───────────────────────────────────────────────────
async def get_columns(db: AsyncSession, table_id: int) -> list[MappingColumnOut]:
    key = f"mapping_table:{table_id}:columns"
    cached = await cache_get(key)
    if cached:
        return [MappingColumnOut.model_validate(r) for r in cached]

    rows = (
        await db.execute(
            select(MappingColumn)
            .where(MappingColumn.mapping_table_id == table_id)
            .order_by(MappingColumn.id)
        )
    ).scalars().all()

    result = [MappingColumnOut.model_validate(r) for r in rows]
    await cache_set(key, [r.model_dump() for r in result], ttl=settings.CACHE_TTL)
    return result


async def get_column(db: AsyncSession, table_id: int, column_id: int) -> MappingColumnOut | None:
    key = f"mapping_table:{table_id}:column:{column_id}"
    cached = await cache_get(key)
    if cached:
        return MappingColumnOut.model_validate(cached)

    obj = (
        await db.execute(
            select(MappingColumn).where(
                MappingColumn.id == column_id,
                MappingColumn.mapping_table_id == table_id,
            )
        )
    ).scalar_one_or_none()

    if obj:
        result = MappingColumnOut.model_validate(obj)
        await cache_set(key, result.model_dump(), ttl=settings.CACHE_TTL)
        return result
    return None


async def create_column(
    db: AsyncSession, table_id: int, payload: MappingColumnCreate
) -> MappingColumnOut:
    obj = MappingColumn(**payload.model_dump(), mapping_table_id=table_id)
    db.add(obj)
    await db.commit()
    await db.refresh(obj)
    await cache_delete(f"mapping_table:{table_id}:columns")
    return MappingColumnOut.model_validate(obj)


async def update_column(
    db: AsyncSession, table_id: int, column_id: int, payload: MappingColumnUpdate
) -> MappingColumnOut | None:
    obj = (
        await db.execute(
            select(MappingColumn).where(
                MappingColumn.id == column_id,
                MappingColumn.mapping_table_id == table_id,
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
        f"mapping_table:{table_id}:columns",
        f"mapping_table:{table_id}:column:{column_id}",
    )
    return MappingColumnOut.model_validate(obj)


async def delete_column(db: AsyncSession, table_id: int, column_id: int) -> bool:
    obj = (
        await db.execute(
            select(MappingColumn).where(
                MappingColumn.id == column_id,
                MappingColumn.mapping_table_id == table_id,
            )
        )
    ).scalar_one_or_none()
    if not obj:
        return False

    await db.delete(obj)
    await db.commit()
    await cache_delete(
        f"mapping_table:{table_id}:columns",
        f"mapping_table:{table_id}:column:{column_id}",
    )
    return True