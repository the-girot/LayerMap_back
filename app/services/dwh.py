"""
Сервисы для DWH-моделей: DWHTable, DWHColumn, LayerMapping, Lineage.

Бизнес-правила маппинга (проверяются на уровне сервиса):
  1. ODS собирается только из одной STG-таблицы.
  2. DDS — из одной или нескольких ODS (может также из STG).
  3. DM — из одной или нескольких DDS/ODS.
  4. Все таблицы в одном маппинге принадлежат одному проекту.
  5. Запрещены циклы в графе lineage.
"""

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.cache import (
    cache_delete,
    cache_delete_pattern,
    cache_get,
    cache_set,
    dwh_column_key,
    dwh_columns_key,
    dwh_table_key,
    dwh_tables_key,
    layer_mapping_key,
    layer_mappings_key,
    lineage_key,
    settings,
)
from app.models.dwh import (
    DWHColumn,
    DWHLayer,
    DWHTable,
    LayerMapping,
    LayerMappingSource,
)
from app.schemas.dwh import (
    DWHColumnCreate,
    DWHColumnOut,
    DWHColumnUpdate,
    DWHTableCreate,
    DWHTableOut,
    DWHTableUpdate,
    LayerMappingCreate,
    LayerMappingOut,
    LayerMappingUpdate,
    LineageMappingEdge,
    LineageOut,
    LineageTableNode,
)

# ══════════════════════════════════════════════════════════════════════
# Общие хелперы
# ══════════════════════════════════════════════════════════════════════


async def _invalidate_project_cache(project_id: int) -> None:
    """Сбросить весь кэш DWH для проекта."""
    await cache_delete_pattern(f"project:{project_id}:dwh_*")
    await cache_delete_pattern(f"project:{project_id}:layer_mapping*")
    await cache_delete(lineage_key(project_id))


# ══════════════════════════════════════════════════════════════════════
# DWHTable
# ══════════════════════════════════════════════════════════════════════


async def get_tables(db: AsyncSession, project_id: int) -> list[DWHTable]:
    """Получить все DWH-таблицы проекта с колонками."""
    key = dwh_tables_key(project_id)
    cached = await cache_get(key)
    if cached is not None:
        return [DWHTable(**item) for item in cached]

    rows = (
        (
            await db.execute(
                select(DWHTable)
                .where(DWHTable.project_id == project_id)
                .options(selectinload(DWHTable.columns))
                .order_by(DWHTable.layer, DWHTable.name)
            )
        )
        .scalars()
        .all()
    )

    await cache_set(
        key,
        [DWHTableOut.model_validate(r).model_dump(mode="json") for r in rows],
        ttl=settings.CACHE_TTL,
    )
    return rows


async def get_table(
    db: AsyncSession, project_id: int, table_id: int
) -> DWHTable | None:
    """Получить одну DWH-таблицу с колонками."""
    key = dwh_table_key(project_id, table_id)
    cached = await cache_get(key)
    if cached is not None:
        return DWHTable(**cached)

    obj = (
        await db.execute(
            select(DWHTable)
            .where(DWHTable.id == table_id, DWHTable.project_id == project_id)
            .options(selectinload(DWHTable.columns))
        )
    ).scalar_one_or_none()

    if obj:
        await cache_set(
            key,
            DWHTableOut.model_validate(obj).model_dump(mode="json"),
            ttl=settings.CACHE_TTL,
        )
    return obj


async def create_table(
    db: AsyncSession, project_id: int, payload: DWHTableCreate
) -> DWHTable:
    """Создать DWH-таблицу."""
    obj = DWHTable(**payload.model_dump(), project_id=project_id)
    db.add(obj)
    await db.commit()
    await db.refresh(obj)
    await db.refresh(obj, attribute_names=["columns"])
    await _invalidate_project_cache(project_id)
    return obj


async def update_table(
    db: AsyncSession, project_id: int, table_id: int, payload: DWHTableUpdate
) -> DWHTable | None:
    """Обновить DWH-таблицу (частичный PATCH)."""
    obj = (
        await db.execute(
            select(DWHTable).where(
                DWHTable.id == table_id,
                DWHTable.project_id == project_id,
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
    await _invalidate_project_cache(project_id)
    return obj


async def delete_table(
    db: AsyncSession, project_id: int, table_id: int
) -> bool:
    """Удалить DWH-таблицу (каскадно удаляет колонки и маппинги)."""
    obj = (
        await db.execute(
            select(DWHTable).where(
                DWHTable.id == table_id,
                DWHTable.project_id == project_id,
            )
        )
    ).scalar_one_or_none()
    if not obj:
        return False

    await db.delete(obj)
    await db.commit()
    await _invalidate_project_cache(project_id)
    return True


# ══════════════════════════════════════════════════════════════════════
# DWHColumn
# ══════════════════════════════════════════════════════════════════════


async def get_columns(db: AsyncSession, table_id: int) -> list[DWHColumn]:
    """Получить колонки DWH-таблицы."""
    key = dwh_columns_key(table_id)
    cached = await cache_get(key)
    if cached is not None:
        return [DWHColumn(**item) for item in cached]

    rows = (
        (
            await db.execute(
                select(DWHColumn)
                .where(DWHColumn.dwh_table_id == table_id)
                .order_by(DWHColumn.id)
            )
        )
        .scalars()
        .all()
    )

    await cache_set(
        key,
        [DWHColumnOut.model_validate(r).model_dump(mode="json") for r in rows],
        ttl=settings.CACHE_TTL,
    )
    return rows


async def get_column(
    db: AsyncSession, table_id: int, column_id: int
) -> DWHColumn | None:
    """Получить одну колонку."""
    key = dwh_column_key(table_id, column_id)
    cached = await cache_get(key)
    if cached is not None:
        return DWHColumn(**cached)

    obj = (
        await db.execute(
            select(DWHColumn).where(
                DWHColumn.id == column_id,
                DWHColumn.dwh_table_id == table_id,
            )
        )
    ).scalar_one_or_none()

    if obj:
        await cache_set(
            key,
            DWHColumnOut.model_validate(obj).model_dump(mode="json"),
            ttl=settings.CACHE_TTL,
        )
    return obj


async def create_column(
    db: AsyncSession, table_id: int, payload: DWHColumnCreate
) -> DWHColumn:
    """Создать колонку в DWH-таблице."""
    obj = DWHColumn(**payload.model_dump(), dwh_table_id=table_id)
    db.add(obj)
    await db.commit()
    await db.refresh(obj)
    await cache_delete(
        dwh_columns_key(table_id),
        dwh_column_key(table_id, obj.id),
    )
    return obj


async def update_column(
    db: AsyncSession, table_id: int, column_id: int, payload: DWHColumnUpdate
) -> DWHColumn | None:
    """Обновить колонку (частичный PATCH)."""
    obj = (
        await db.execute(
            select(DWHColumn).where(
                DWHColumn.id == column_id,
                DWHColumn.dwh_table_id == table_id,
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
        dwh_columns_key(table_id),
        dwh_column_key(table_id, column_id),
    )
    return obj


async def delete_column(
    db: AsyncSession, table_id: int, column_id: int
) -> bool:
    """Удалить колонку."""
    obj = (
        await db.execute(
            select(DWHColumn).where(
                DWHColumn.id == column_id,
                DWHColumn.dwh_table_id == table_id,
            )
        )
    ).scalar_one_or_none()
    if not obj:
        return False

    await db.delete(obj)
    await db.commit()
    await cache_delete(
        dwh_columns_key(table_id),
        dwh_column_key(table_id, column_id),
    )
    return True


# ══════════════════════════════════════════════════════════════════════
# LayerMapping — бизнес-правила
# ══════════════════════════════════════════════════════════════════════


async def _validate_mapping_rules(
    db: AsyncSession,
    project_id: int,
    target_table: DWHTable,
    source_tables: list[DWHTable],
    mapping_id: int | None = None,  # передаётся при update для проверки циклов
) -> None:
    """Проверить бизнес-правила маппинга.

    Args:
        db: сессия БД.
        project_id: ID проекта.
        target_table: целевая DWH-таблица.
        source_tables: список исходных DWH-таблиц.
        mapping_id: ID текущего маппинга (для исключения self-check при update).
    """
    target_layer = target_table.layer

    # ── Правило 1: все таблицы должны принадлежать одному проекту ──
    for st in source_tables:
        if st.project_id != project_id:
            raise HTTPException(
                status_code=422,
                detail=f"Таблица '{st.name}' (id={st.id}) не принадлежит проекту {project_id}",
            )

    # ── Правило 2: ODS собирается только из одной STG ──
    if target_layer == DWHLayer.ODS:
        if len(source_tables) != 1:
            raise HTTPException(
                status_code=422,
                detail="ODS-таблица должна собираться ровно из одной STG-таблицы",
            )
        if source_tables[0].layer != DWHLayer.STG:
            raise HTTPException(
                status_code=422,
                detail="ODS-таблица может собираться только из STG-таблицы",
            )

    # ── Правило 3: DDS может собираться из ODS (или STG) ──
    if target_layer == DWHLayer.DDS:
        allowed_layers = {DWHLayer.ODS, DWHLayer.STG}
        for st in source_tables:
            if st.layer not in allowed_layers:
                raise HTTPException(
                    status_code=422,
                    detail=f"DDS-таблица '{target_table.name}' не может собираться "
                    f"из таблицы слоя {st.layer.value} (разрешены только ODS, STG)",
                )

    # ── Правило 4: DM может собираться из DDS/ODS ──
    if target_layer == DWHLayer.DM:
        allowed_layers = {DWHLayer.DDS, DWHLayer.ODS}
        for st in source_tables:
            if st.layer not in allowed_layers:
                raise HTTPException(
                    status_code=422,
                    detail=f"DM-таблица '{target_table.name}' не может собираться "
                    f"из таблицы слоя {st.layer.value} (разрешены только DDS, ODS)",
                )

    # ── Правило 5: STG не может быть целью маппинга ──
    if target_layer == DWHLayer.STG:
        raise HTTPException(
            status_code=422,
            detail="STG-таблица не может быть целью маппинга (данные поступают напрямую из источников)",
        )

    # ── Правило 6: запрет циклов в графе ──
    await _check_cycles(db, project_id, target_table.id, source_tables, mapping_id)


async def _check_cycles(
    db: AsyncSession,
    project_id: int,
    target_table_id: int,
    source_tables: list[DWHTable],
    mapping_id: int | None,
) -> None:
    """Проверить, что маппинг не создаёт циклов в графе lineage.

    Алгоритм: BFS от всех source_tables вниз по графу.
    Если при обходе мы натыкаемся на target_table — есть цикл.
    """
    # Собираем все маппинги проекта с источниками (один запрос)
    stmt = (
        select(LayerMapping)
        .where(LayerMapping.project_id == project_id)
        .options(selectinload(LayerMapping.sources))
    )
    if mapping_id is not None:
        stmt = stmt.where(LayerMapping.id != mapping_id)

    all_mappings = (await db.execute(stmt)).scalars().all()

    # Строим граф: source_table_id -> target_table_id
    mapping_by_source: dict[int, int] = {}
    for mp in all_mappings:
        for src in mp.sources:
            mapping_by_source[src.source_table_id] = mp.target_table_id

    # BFS от каждой source таблицы
    visited: set[int] = set()
    queue = [st.id for st in source_tables]

    while queue:
        current = queue.pop(0)
        if current == target_table_id:
            raise HTTPException(
                status_code=422,
                detail="Обнаружен цикл в графе lineage: добавляемая зависимость "
                "создаёт обратную связь",
            )
        if current in visited:
            continue
        visited.add(current)

        # Идём дальше по графу от current
        if current in mapping_by_source:
            next_id = mapping_by_source[current]
            if next_id not in visited:
                queue.append(next_id)


async def get_mappings(db: AsyncSession, project_id: int) -> list[LayerMapping]:
    """Получить все маппинги проекта с источниками и целевыми таблицами."""
    key = layer_mappings_key(project_id)
    cached = await cache_get(key)
    if cached is not None:
        return [LayerMapping(**item) for item in cached]

    rows = (
        (
            await db.execute(
                select(LayerMapping)
                .where(LayerMapping.project_id == project_id)
                .options(
                    selectinload(LayerMapping.sources),
                    selectinload(LayerMapping.target_table).selectinload(
                        DWHTable.columns
                    ),
                )
                .order_by(LayerMapping.id)
            )
        )
        .scalars()
        .all()
    )

    await cache_set(
        key,
        [LayerMappingOut.model_validate(r).model_dump(mode="json") for r in rows],
        ttl=settings.CACHE_TTL,
    )
    return rows


async def get_mapping(
    db: AsyncSession, project_id: int, mapping_id: int
) -> LayerMapping | None:
    """Получить один маппинг с источниками."""
    key = layer_mapping_key(project_id, mapping_id)
    cached = await cache_get(key)
    if cached is not None:
        return LayerMapping(**cached)

    obj = (
        await db.execute(
            select(LayerMapping)
            .where(
                LayerMapping.id == mapping_id,
                LayerMapping.project_id == project_id,
            )
            .options(
                selectinload(LayerMapping.sources),
                selectinload(LayerMapping.target_table).selectinload(
                    DWHTable.columns
                ),
            )
        )
    ).scalar_one_or_none()

    if obj:
        await cache_set(
            key,
            LayerMappingOut.model_validate(obj).model_dump(mode="json"),
            ttl=settings.CACHE_TTL,
        )
    return obj


async def create_mapping(
    db: AsyncSession, project_id: int, payload: LayerMappingCreate
) -> LayerMapping:
    """Создать маппинг с проверкой бизнес-правил.

    Шаги:
    1. Загрузить целевую таблицу.
    2. Загрузить исходные таблицы.
    3. Проверить бизнес-правила.
    4. Создать маппинг и связи с источниками.
    """
    # 1. Целевая таблица
    target = (
        await db.execute(
            select(DWHTable).where(
                DWHTable.id == payload.target_table_id,
                DWHTable.project_id == project_id,
            )
        )
    ).scalar_one_or_none()
    if not target:
        raise HTTPException(
            status_code=404,
            detail=f"Целевая таблица (id={payload.target_table_id}) не найдена в проекте",
        )

    # 2. Исходные таблицы
    source_tables: list[DWHTable] = []
    for sid in payload.source_table_ids:
        st = (
            await db.execute(
                select(DWHTable).where(
                    DWHTable.id == sid,
                    DWHTable.project_id == project_id,
                )
            )
        ).scalar_one_or_none()
        if not st:
            raise HTTPException(
                status_code=404,
                detail=f"Исходная таблица (id={sid}) не найдена в проекте",
            )
        source_tables.append(st)

    # 3. Проверка правил
    await _validate_mapping_rules(db, project_id, target, source_tables)

    # 4. Создание
    mapping = LayerMapping(
        project_id=project_id,
        target_table_id=payload.target_table_id,
        transformation=payload.transformation,
        algorithm=payload.algorithm,
    )
    db.add(mapping)
    await db.flush()

    for st in source_tables:
        lms = LayerMappingSource(
            mapping_id=mapping.id, source_table_id=st.id
        )
        db.add(lms)

    await db.commit()
    await db.refresh(mapping)
    # Явно загрузим связи
    await db.refresh(mapping, attribute_names=["sources"])
    await _invalidate_project_cache(project_id)
    return mapping


async def update_mapping(
    db: AsyncSession,
    project_id: int,
    mapping_id: int,
    payload: LayerMappingUpdate,
) -> LayerMapping | None:
    """Обновить маппинг (частичный PATCH для transformation/algorithm).

    source_table_ids не обновляются через этот метод — для изменения
    источников нужно удалить и создать маппинг заново.
    """
    obj = (
        await db.execute(
            select(LayerMapping)
            .where(
                LayerMapping.id == mapping_id,
                LayerMapping.project_id == project_id,
            )
            .options(selectinload(LayerMapping.sources))
        )
    ).scalar_one_or_none()
    if not obj:
        return None

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(obj, field, value)

    await db.commit()
    await db.refresh(obj)
    await db.refresh(obj, attribute_names=["sources"])
    await _invalidate_project_cache(project_id)
    return obj


async def delete_mapping(
    db: AsyncSession, project_id: int, mapping_id: int
) -> bool:
    """Удалить маппинг (каскадно удаляет LayerMappingSource)."""
    obj = (
        await db.execute(
            select(LayerMapping).where(
                LayerMapping.id == mapping_id,
                LayerMapping.project_id == project_id,
            )
        )
    ).scalar_one_or_none()
    if not obj:
        return False

    await db.delete(obj)
    await db.commit()
    await _invalidate_project_cache(project_id)
    return True


# ══════════════════════════════════════════════════════════════════════
# Lineage — агрегированный ответ
# ══════════════════════════════════════════════════════════════════════


async def get_lineage(db: AsyncSession, project_id: int) -> LineageOut:
    """Получить полный граф lineage для проекта (с кэшированием).

    Формат ответа оптимизирован для frontend:
    - tables: все DWH-таблицы проекта с колонками.
    - mappings: список маппингов с target_table_id и source_table_ids.
    """
    key = lineage_key(project_id)
    cached = await cache_get(key)
    if cached is not None:
        return LineageOut(**cached)

    # Загружаем все таблицы с колонками
    tables = (
        (
            await db.execute(
                select(DWHTable)
                .where(DWHTable.project_id == project_id)
                .options(selectinload(DWHTable.columns))
                .order_by(DWHTable.layer, DWHTable.name)
            )
        )
        .scalars()
        .all()
    )

    # Загружаем все маппинги с источниками
    mappings = (
        (
            await db.execute(
                select(LayerMapping)
                .where(LayerMapping.project_id == project_id)
                .options(selectinload(LayerMapping.sources))
                .order_by(LayerMapping.id)
            )
        )
        .scalars()
        .all()
    )

    # Собираем ответ
    table_nodes = [
        LineageTableNode(
            id=t.id,
            layer=t.layer,
            name=t.name,
            description=t.description,
            columns=[
                DWHColumnOut.model_validate(c) for c in t.columns
            ],
        )
        for t in tables
    ]

    mapping_edges = [
        LineageMappingEdge(
            id=m.id,
            target_table_id=m.target_table_id,
            source_table_ids=[s.source_table_id for s in m.sources],
            transformation=m.transformation,
            algorithm=m.algorithm,
        )
        for m in mappings
    ]

    result = LineageOut(tables=table_nodes, mappings=mapping_edges)

    await cache_set(
        key,
        result.model_dump(mode="json"),
        ttl=settings.CACHE_TTL,
    )
    return result
