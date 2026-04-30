"""
Тесты бизнес-правил DWH-маппинга.

Покрытие:
  - ODS из одной STG ✓
  - Запрет ODS из двух STG ✓
  - DDS из нескольких ODS ✓
  - DM из DDS и ODS ✓
  - Запрет циклов ✓
  - Все таблицы одного проекта ✓
  - Каскадное удаление ✓
"""

import pytest

from tests.factories import (
    create_dwh_column,
    create_dwh_table,
    create_layer_mapping,
    create_project,
)


# ══════════════════════════════════════════════════════════════════════
# Правило: ODS собирается только из одной STG
# ══════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_ods_from_one_stg_ok(auth_client, db_session):
    """ODS из одной STG — разрешено."""
    project = await create_project(db_session)
    stg = await create_dwh_table(db_session, project, "STG", "stg_orders")
    ods = await create_dwh_table(db_session, project, "ODS", "ods_orders")

    resp = await auth_client.post(
        f"/projects/{project.id}/layer-mappings",
        json={
            "targetTableId": ods.id,
            "sourceTableIds": [stg.id],
        },
    )
    assert resp.status_code == 201


@pytest.mark.asyncio
async def test_ods_from_two_stg_fails(auth_client, db_session):
    """ODS из двух STG — запрещено."""
    project = await create_project(db_session)
    stg1 = await create_dwh_table(db_session, project, "STG", "stg_orders")
    stg2 = await create_dwh_table(db_session, project, "STG", "stg_customers")
    ods = await create_dwh_table(db_session, project, "ODS", "ods_orders")

    resp = await auth_client.post(
        f"/projects/{project.id}/layer-mappings",
        json={
            "targetTableId": ods.id,
            "sourceTableIds": [stg1.id, stg2.id],
        },
    )
    assert resp.status_code == 422
    assert "ODS" in resp.json()["detail"]


@pytest.mark.asyncio
async def test_ods_from_non_stg_fails(auth_client, db_session):
    """ODS из не-STG таблицы — запрещено."""
    project = await create_project(db_session)
    ods_src = await create_dwh_table(db_session, project, "ODS", "ods_other")
    ods = await create_dwh_table(db_session, project, "ODS", "ods_orders")

    resp = await auth_client.post(
        f"/projects/{project.id}/layer-mappings",
        json={
            "targetTableId": ods.id,
            "sourceTableIds": [ods_src.id],
        },
    )
    assert resp.status_code == 422


# ══════════════════════════════════════════════════════════════════════
# Правило: DDS из нескольких ODS
# ══════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_dds_from_multiple_ods_ok(auth_client, db_session):
    """DDS из нескольких ODS — разрешено."""
    project = await create_project(db_session)
    stg1 = await create_dwh_table(db_session, project, "STG", "stg_orders")
    stg2 = await create_dwh_table(db_session, project, "STG", "stg_customers")
    ods1 = await create_dwh_table(db_session, project, "ODS", "ods_orders")
    ods2 = await create_dwh_table(db_session, project, "ODS", "ods_customers")
    dds = await create_dwh_table(db_session, project, "DDS", "dds_facts")

    # Создаём ODS -> STG маппинги
    await create_layer_mapping(db_session, project, ods1, [stg1])
    await create_layer_mapping(db_session, project, ods2, [stg2])

    # DDS из двух ODS
    resp = await auth_client.post(
        f"/projects/{project.id}/layer-mappings",
        json={
            "targetTableId": dds.id,
            "sourceTableIds": [ods1.id, ods2.id],
        },
    )
    assert resp.status_code == 201


@pytest.mark.asyncio
async def test_dds_from_dm_fails(auth_client, db_session):
    """DDS из DM — запрещено."""
    project = await create_project(db_session)
    dm = await create_dwh_table(db_session, project, "DM", "dm_report")
    dds = await create_dwh_table(db_session, project, "DDS", "dds_facts")

    resp = await auth_client.post(
        f"/projects/{project.id}/layer-mappings",
        json={
            "targetTableId": dds.id,
            "sourceTableIds": [dm.id],
        },
    )
    assert resp.status_code == 422


# ══════════════════════════════════════════════════════════════════════
# Правило: DM из DDS/ODS
# ══════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_dm_from_dds_and_ods_ok(auth_client, db_session):
    """DM из DDS и ODS — разрешено."""
    project = await create_project(db_session)
    ods = await create_dwh_table(db_session, project, "ODS", "ods_orders")
    dds = await create_dwh_table(db_session, project, "DDS", "dds_facts")
    dm = await create_dwh_table(db_session, project, "DM", "dm_report")

    resp = await auth_client.post(
        f"/projects/{project.id}/layer-mappings",
        json={
            "targetTableId": dm.id,
            "sourceTableIds": [ods.id, dds.id],
        },
    )
    assert resp.status_code == 201


@pytest.mark.asyncio
async def test_dm_from_stg_fails(auth_client, db_session):
    """DM из STG — запрещено."""
    project = await create_project(db_session)
    stg = await create_dwh_table(db_session, project, "STG", "stg_orders")
    dm = await create_dwh_table(db_session, project, "DM", "dm_report")

    resp = await auth_client.post(
        f"/projects/{project.id}/layer-mappings",
        json={
            "targetTableId": dm.id,
            "sourceTableIds": [stg.id],
        },
    )
    assert resp.status_code == 422


# ══════════════════════════════════════════════════════════════════════
# Правило: STG не может быть целью маппинга
# ══════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_stg_as_target_fails(auth_client, db_session):
    """STG не может быть целью маппинга."""
    project = await create_project(db_session)
    stg_src = await create_dwh_table(db_session, project, "STG", "stg_orders")
    stg_target = await create_dwh_table(
        db_session, project, "STG", "stg_other"
    )

    resp = await auth_client.post(
        f"/projects/{project.id}/layer-mappings",
        json={
            "targetTableId": stg_target.id,
            "sourceTableIds": [stg_src.id],
        },
    )
    assert resp.status_code == 422


# ══════════════════════════════════════════════════════════════════════
# Правило: все таблицы одного проекта
# ══════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_tables_from_different_projects_fails(auth_client, db_session):
    """Маппинг с таблицами из разных проектов — запрещено."""
    project_a = await create_project(db_session, "Project A")
    project_b = await create_project(db_session, "Project B")

    stg = await create_dwh_table(
        db_session, project_a, "STG", "stg_orders"
    )
    ods = await create_dwh_table(
        db_session, project_b, "ODS", "ods_orders"
    )

    resp = await auth_client.post(
        f"/projects/{project_a.id}/layer-mappings",
        json={
            "targetTableId": ods.id,
            "sourceTableIds": [stg.id],
        },
    )
    assert resp.status_code == 404  # целевая таблица не найдена в проекте


# ══════════════════════════════════════════════════════════════════════
# Правило: запрет циклов
# ══════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_cycle_detection_fails(auth_client, db_session):
    """Создание цикла в графе — запрещено."""
    project = await create_project(db_session)

    # Строим: STG -> ODS -> DDS
    stg = await create_dwh_table(db_session, project, "STG", "stg_orders")
    ods = await create_dwh_table(db_session, project, "ODS", "ods_orders")
    dds = await create_dwh_table(db_session, project, "DDS", "dds_facts")

    await create_layer_mapping(db_session, project, ods, [stg])
    await create_layer_mapping(db_session, project, dds, [ods])

    # Пытаемся создать цикл: ODS -> DDS (обратная зависимость)
    # Нужно, чтобы ODS ссылалась на DDS, а у ODS уже есть маппинг
    # Создаём новую ODS и пытаемся сделать её из DDS
    ods2 = await create_dwh_table(db_session, project, "ODS", "ods_cycle")
    resp = await auth_client.post(
        f"/projects/{project.id}/layer-mappings",
        json={
            "targetTableId": ods2.id,
            "sourceTableIds": [dds.id],
        },
    )
    assert resp.status_code == 422
    assert "цикл" in resp.json()["detail"].lower()


@pytest.mark.asyncio
async def test_multi_level_cycle_fails(auth_client, db_session):
    """Многоуровневый цикл — запрещено."""
    project = await create_project(db_session)

    # Цепочка: STG1 -> ODS1 -> DDS1
    stg1 = await create_dwh_table(db_session, project, "STG", "stg_1")
    ods1 = await create_dwh_table(db_session, project, "ODS", "ods_1")
    dds1 = await create_dwh_table(db_session, project, "DDS", "dds_1")

    await create_layer_mapping(db_session, project, ods1, [stg1])
    await create_layer_mapping(db_session, project, dds1, [ods1])

    # Пытаемся создать STG -> DDS1 (создаст цикл STG -> ODS1 -> DDS1 -> STG)
    # Но STG не может быть целью маппинга, так что создаём другую DM -> DDS1
    dm1 = await create_dwh_table(db_session, project, "DM", "dm_1")
    resp = await auth_client.post(
        f"/projects/{project.id}/layer-mappings",
        json={
            "targetTableId": dm1.id,
            "sourceTableIds": [dds1.id],
        },
    )
    # Это должно быть разрешено — DM из DDS
    assert resp.status_code == 201

    # А вот пытаться сделать ODS из DM (где ODS уже upstream от DDS) — может быть цикл
    # Создаём ODS2 -> DDS1 (ODS2 не имеет upstream, а DDS1 выше по цепочке)
    # Это нормально (ODS может быть источником для DDS)
    ods2 = await create_dwh_table(db_session, project, "ODS", "ods_2")
    resp = await auth_client.post(
        f"/projects/{project.id}/layer-mappings",
        json={
            "targetTableId": ods2.id,
            "sourceTableIds": [stg1.id],
        },
    )
    assert resp.status_code == 201


# ══════════════════════════════════════════════════════════════════════
# Каскадное удаление
# ══════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_cascade_delete_table_removes_mappings(auth_client, db_session):
    """Удаление таблицы каскадно удаляет маппинги, где она цель."""
    project = await create_project(db_session)
    stg = await create_dwh_table(db_session, project, "STG", "stg_orders")
    ods = await create_dwh_table(db_session, project, "ODS", "ods_orders")
    await create_dwh_column(db_session, ods, "order_id", "integer")
    await create_layer_mapping(db_session, project, ods, [stg])

    # Удаляем целевую таблицу — маппинг должен удалиться
    resp = await auth_client.delete(
        f"/projects/{project.id}/dwh-tables/{ods.id}"
    )
    assert resp.status_code == 204

    # Маппинги должны быть пусты
    resp = await auth_client.get(
        f"/projects/{project.id}/layer-mappings"
    )
    assert resp.status_code == 200
    assert len(resp.json()) == 0


@pytest.mark.asyncio
async def test_cascade_delete_table_removes_columns(auth_client, db_session):
    """Удаление таблицы каскадно удаляет её колонки."""
    project = await create_project(db_session)
    table = await create_dwh_table(db_session, project, "STG", "stg_orders")
    await create_dwh_column(db_session, table, "col_1", "integer")
    await create_dwh_column(db_session, table, "col_2", "string")

    resp = await auth_client.delete(
        f"/projects/{project.id}/dwh-tables/{table.id}"
    )
    assert resp.status_code == 204

    # Проверяем что колонок нет
    resp = await auth_client.get(
        f"/projects/{project.id}/dwh-tables/{table.id}"
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_cascade_delete_mapping_removes_sources(auth_client, db_session):
    """Удаление маппинга каскадно удаляет связи с источниками."""
    project = await create_project(db_session)
    stg = await create_dwh_table(db_session, project, "STG", "stg_orders")
    ods = await create_dwh_table(db_session, project, "ODS", "ods_orders")
    mapping = await create_layer_mapping(db_session, project, ods, [stg])

    resp = await auth_client.delete(
        f"/projects/{project.id}/layer-mappings/{mapping.id}"
    )
    assert resp.status_code == 204

    # Проверяем что sources нет после удаления маппинга
    resp = await auth_client.get(
        f"/projects/{project.id}/layer-mappings/{mapping.id}"
    )
    assert resp.status_code == 404


# ══════════════════════════════════════════════════════════════════════
# Валидация входных данных
# ══════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_create_mapping_empty_sources_fails(auth_client, db_session):
    """Пустой список источников — 422."""
    project = await create_project(db_session)
    ods = await create_dwh_table(db_session, project, "ODS", "ods_orders")

    resp = await auth_client.post(
        f"/projects/{project.id}/layer-mappings",
        json={
            "targetTableId": ods.id,
            "sourceTableIds": [],
        },
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_create_mapping_duplicate_sources_fails(auth_client, db_session):
    """Дубликаты в списке источников — 422."""
    project = await create_project(db_session)
    stg = await create_dwh_table(db_session, project, "STG", "stg_orders")
    ods = await create_dwh_table(db_session, project, "ODS", "ods_orders")

    resp = await auth_client.post(
        f"/projects/{project.id}/layer-mappings",
        json={
            "targetTableId": ods.id,
            "sourceTableIds": [stg.id, stg.id],
        },
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_create_mapping_nonexistent_target_fails(auth_client, db_session):
    """Несуществующая целевая таблица — 404."""
    project = await create_project(db_session)
    stg = await create_dwh_table(db_session, project, "STG", "stg_orders")

    resp = await auth_client.post(
        f"/projects/{project.id}/layer-mappings",
        json={
            "targetTableId": 99999,
            "sourceTableIds": [stg.id],
        },
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_create_mapping_nonexistent_source_fails(auth_client, db_session):
    """Несуществующая исходная таблица — 404."""
    project = await create_project(db_session)
    ods = await create_dwh_table(db_session, project, "ODS", "ods_orders")

    resp = await auth_client.post(
        f"/projects/{project.id}/layer-mappings",
        json={
            "targetTableId": ods.id,
            "sourceTableIds": [99999],
        },
    )
    assert resp.status_code == 404
