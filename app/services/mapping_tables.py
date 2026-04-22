from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.cache import (
    cache_delete,
    cache_get,
    cache_set,
    mapping_tables_key,
    settings,
)
from app.models.mapping_table import MappingColumn, MappingTable
from app.models.source import Source
from app.schemas.mapping_table import (
    MappingColumnCreate,
    MappingColumnOut,
    MappingColumnUpdate,
    MappingTableCreate,
    MappingTableOut,
    MappingTableUpdate,
)

# ── Таблицы ──────────────────────────────────────────────────────────────────


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

    # Один запрос для всех source_id
    table_ids = [r.id for r in rows]
    sources = (
        await db.execute(
            select(Source).where(Source.mapping_table_id.in_(table_ids))
        )
    ).scalars().all()
    source_map = {s.mapping_table_id: s.id for s in sources}

    result = []
    for row in rows:
        item = MappingTableOut.model_validate(row)
        item.source_id = source_map.get(row.id)
        result.append(item)

    await cache_set(key, [r.model_dump() for r in result], ttl=settings.CACHE_TTL)
    return result

async def get_one(
    db: AsyncSession, project_id: int, table_id: int
) -> MappingTableOut | None:
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
        source = (
            await db.execute(
                select(Source).where(Source.mapping_table_id == obj.id)
            )
        ).scalar_one_or_none()

        result = MappingTableOut.model_validate(obj)
        result.source_id = source.id if source else None
        await cache_set(key, result.model_dump(), ttl=settings.CACHE_TTL)
        return result
    return None

async def create(
    db: AsyncSession,
    project_id: int,
    payload: MappingTableCreate,
) -> MappingTableOut:
    source_id = payload.source_id  # сохранить до model_dump
    data = payload.model_dump(exclude={"source_id"})
    obj = MappingTable(**data, project_id=project_id)
    db.add(obj)
    await db.flush()  # получаем obj.id до commit

    # Привязываем источник к созданной таблице
    if source_id is not None:
        source = (
            await db.execute(
                select(Source).where(
                    Source.id == source_id,
                    Source.project_id == project_id,
                )
            )
        ).scalar_one_or_none()
        if source:
            source.mapping_table_id = obj.id

    await db.commit()
    await db.refresh(obj)
    await db.refresh(obj, attribute_names=["columns"])
    await cache_delete(mapping_tables_key(project_id))

    result = MappingTableOut.model_validate(obj)
    result.source_id = source_id  # вернуть в ответе
    return result


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

    update_data = payload.model_dump(exclude_unset=True)
    new_source_id = update_data.pop("source_id", ...)

    for field, value in update_data.items():
        setattr(obj, field, value)

    if new_source_id is not ...:
        old_source = (
            await db.execute(
                select(Source).where(
                    Source.mapping_table_id == table_id,
                    Source.project_id == project_id,
                )
            )
        ).scalar_one_or_none()
        if old_source:
            old_source.mapping_table_id = None

        if new_source_id is not None:
            new_source = (
                await db.execute(
                    select(Source).where(
                        Source.id == new_source_id,
                        Source.project_id == project_id,
                    )
                )
            ).scalar_one_or_none()
            if new_source:
                new_source.mapping_table_id = table_id

    await db.commit()
    await db.refresh(obj)
    await db.refresh(obj, attribute_names=["columns"])
    await cache_delete(
        mapping_tables_key(project_id),
        f"project:{project_id}:mapping_table:{table_id}",
        f"mapping_table:{table_id}:columns",
    )

    current_source = (
        await db.execute(
            select(Source).where(Source.mapping_table_id == table_id)
        )
    ).scalar_one_or_none()

    result = MappingTableOut.model_validate(obj)
    result.source_id = current_source.id if current_source else None
    return result


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
        f"mapping_table:{table_id}:columns",
    )
    return True


async def get_by_source(
    db: AsyncSession,
    project_id: int,
    source_id: int,
) -> list[MappingTableOut]:
    # Находим mapping_table_id у источника
    source = (
        await db.execute(
            select(Source).where(
                Source.id == source_id,
                Source.project_id == project_id,
            )
        )
    ).scalar_one_or_none()

    if not source or source.mapping_table_id is None:
        return []

    rows = (
        (
            await db.execute(
                select(MappingTable)
                .where(
                    MappingTable.id == source.mapping_table_id,
                    MappingTable.project_id == project_id,
                )
                .options(selectinload(MappingTable.columns))
                .order_by(MappingTable.id)
            )
        )
        .scalars()
        .all()
    )

    return [MappingTableOut.model_validate(r) for r in rows]


# ── Колонки ──────────────────────────────────────────────────────────────────


async def get_columns(db: AsyncSession, table_id: int) -> list[MappingColumnOut]:
    key = f"mapping_table:{table_id}:columns"
    cached = await cache_get(key)
    if cached:
        return [MappingColumnOut.model_validate(r) for r in cached]

    rows = (
        (
            await db.execute(
                select(MappingColumn)
                .where(MappingColumn.mapping_table_id == table_id)
                .order_by(MappingColumn.id)
            )
        )
        .scalars()
        .all()
    )

    result = [MappingColumnOut.model_validate(r) for r in rows]
    await cache_set(key, [r.model_dump() for r in result], ttl=settings.CACHE_TTL)
    return result


async def get_column(
    db: AsyncSession, table_id: int, column_id: int
) -> MappingColumnOut | None:
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
